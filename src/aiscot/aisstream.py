#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# AISCOT aisstream.py
#
# Copyright Sensors & Signals LLC https://www.snstac.com
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""AISCOT AISStream.io Integration."""

import asyncio
import json
import logging
import os
import time
import threading
from configparser import ConfigParser
from typing import List, Optional, Dict, Any

import websockets

import aiscot

Logger = logging.getLogger(__name__)


class VesselRegistry:
    """Vessel registry to maintain vessel names across different AIS message types.

    This registry uses a simple in-memory dictionary to store vessel names from
    ShipStaticData messages and apply them to position reports.
    """

    def __init__(self, cache_file: Optional[str] = None) -> None:
        """Initialize the vessel registry.

        Parameters
        ----------
        cache_file : Optional[str]
            Path to the cache file for persisting vessel names between restarts,
            or None to keep everything in memory only
        """
        self.cache_file = cache_file
        self._lock = threading.RLock()

        # Initialize the vessel name dictionary - maps MMSI -> name
        self.vessel_names = {}

        # Load cached vessel names if available and a cache file is specified
        if self.cache_file:
            self._load_cache()

        Logger.info(
            "Vessel registry initialized with %d vessel names", len(
                self.vessel_names))

    def _load_cache(self) -> None:
        """Load vessel names from the cache file if it exists."""
        if not self.cache_file:
            return

        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r") as f:
                    self.vessel_names = json.load(f)
                Logger.info(
                    "Loaded %d vessel names from cache file", len(
                        self.vessel_names))
            except Exception as e:
                Logger.error("Error loading vessel name cache: %s", e)

    def _save_cache(self) -> None:
        """Save vessel names to the cache file."""
        if not self.cache_file:
            return

        try:
            with open(self.cache_file, "w") as f:
                json.dump(self.vessel_names, f)
            Logger.debug("Saved %d vessel names to cache file", len(self.vessel_names))
        except Exception as e:
            Logger.error("Error saving vessel name cache: %s", e)

    def update_vessel_static(self, data: Dict[str, Any]) -> None:
        """Update vessel static information from ShipStaticData.

        Parameters
        ----------
        data : Dict[str, Any]
            Dictionary containing vessel static information
        """
        mmsi = str(data.get("mmsi", ""))
        if not mmsi:
            return

        # Extract and clean the name
        name = str(data.get("name", "")).strip()
        if not name:
            return

        with self._lock:
            # Store the vessel name
            self.vessel_names[mmsi] = name

            # Save to cache file every 5 new entries, but only if cache file is
            # specified
            if self.cache_file and len(self.vessel_names) % 5 == 0:
                self._save_cache()

        Logger.info("Updated vessel name: MMSI=%s, Name=%s", mmsi, name)

    def enrich_message(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich an AIS message with vessel name from the registry.

        Parameters
        ----------
        msg : Dict[str, Any]
            Original AIS message

        Returns
        -------
        Dict[str, Any]
            Enriched message with vessel name if available
        """
        mmsi = str(msg.get("mmsi", ""))
        if not mmsi:
            return msg

        # Don't bother if message already has a name
        if msg.get("name"):
            return msg

        # Create a copy to avoid modifying the original
        enriched = msg.copy()

        with self._lock:
            # Look up the vessel name
            if mmsi in self.vessel_names:
                name = self.vessel_names[mmsi]
                Logger.debug("Found vessel in registry: MMSI=%s, Name=%s", mmsi, name)
                enriched["name"] = name
                Logger.debug("Enriched message with vessel name: %s -> %s", mmsi, name)
            else:
                Logger.debug("No vessel name found in registry for MMSI: %s", mmsi)

        return enriched

    def print_registry(self, limit: int = 20) -> None:
        """Print information about vessels in the registry.

        Parameters
        ----------
        limit : int
            Maximum number of vessels to print
        """
        with self._lock:
            if not self.vessel_names:
                Logger.info("Vessel registry is empty")
                return

            # Sort by MMSI for consistent output
            sorted_vessels = sorted(self.vessel_names.items())
            vessels_to_print = sorted_vessels[:limit]

            Logger.info("=== Vessel Registry Contents ===")
            for mmsi, name in vessels_to_print:
                Logger.info("MMSI: %s, Name: %s", mmsi, name or "None")

            if len(sorted_vessels) > limit:
                Logger.info("... and %d more vessels", len(sorted_vessels) - limit)

            Logger.info("=== End of Registry Listing ===")
            Logger.info("Total vessels in registry: %d", len(self.vessel_names))


# Singleton registry instance for the application
_registry_instance = None
_registry_lock = threading.Lock()


def get_registry(cache_file: Optional[str] = None) -> VesselRegistry:
    """Get the singleton registry instance.

    Parameters
    ----------
    cache_file : Optional[str]
        Path to the cache file, or None for in-memory only

    Returns
    -------
    VesselRegistry
        The singleton registry instance
    """
    global _registry_instance

    with _registry_lock:
        if _registry_instance is None:
            _registry_instance = VesselRegistry(cache_file)

        return _registry_instance


class AISStreamClient:
    """Client for AISStream.io websocket connection."""

    def __init__(self, queue: asyncio.Queue, config: ConfigParser) -> None:
        """Initialize the AISStream client.

        Parameters
        ----------
        queue : asyncio.Queue
            Queue to put CoT events into
        config : ConfigParser
            Configuration object
        """
        self.queue = queue
        self.config = config
        self._logger = Logger

        if self.config.getboolean("DEBUG", False):
            self._logger.setLevel(logging.DEBUG)

        self.api_key = self.config.get("AISSTREAM_API_KEY", "")
        if not self.api_key:
            self._logger.error("No AISSTREAM_API_KEY provided in config")

        # Get bounding box coordinates from config
        self.bbox_lon_min = float(self.config.get("BBOX_LON_MIN", -11))
        self.bbox_lat_min = float(self.config.get("BBOX_LAT_MIN", 178))
        self.bbox_lon_max = float(self.config.get("BBOX_LON_MAX", 30))
        self.bbox_lat_max = float(self.config.get("BBOX_LAT_MAX", 74))

        # Get message types to filter (optional)
        self.message_types = self.config.get("AISSTREAM_MESSAGE_TYPES", "")
        if self.message_types:
            self.message_types = [mt.strip() for mt in self.message_types.split(",")]
        else:
            self.message_types = []

        self.known_craft_db: List[Any] = []
        known_craft = self.config.get("KNOWN_CRAFT")
        if known_craft:
            self._logger.info("Using KNOWN_CRAFT: %s", known_craft)
            self.known_craft_db = aiscot.get_known_craft(known_craft)

        # Initialize vessel registry
        vessel_cache = self.config.get("VESSEL_CACHE_FILE", None)
        self.registry = get_registry(vessel_cache)
        if vessel_cache:
            self._logger.info("Using vessel registry with cache file: %s", vessel_cache)
        else:
            self._logger.info("Using in-memory vessel registry (no persistence)")

        # For periodic registry stats
        self.last_registry_print = 0
        self.registry_print_interval = 60  # Print registry info every 60 seconds

    async def connect(self) -> None:
        """Connect to AISStream.io websocket and process messages."""
        self._logger.info("Connecting to AISStream.io websocket")

        websocket_url = "wss://stream.aisstream.io/v0/stream"

        # IMPORTANT: Format MUST be [[[lat_min, lon_min], [lat_max, lon_max]]]
        # Per AISStream.io docs, coordinate format is [latitude, longitude]
        subscribe_message = {
            "APIKey": self.api_key,
            "BoundingBoxes": [
                [
                    [self.bbox_lat_min, self.bbox_lon_min],
                    [self.bbox_lat_max, self.bbox_lon_max],
                ]
            ],
        }

        # Add message type filter if specified - using proper key name
        if self.message_types:
            subscribe_message["FilterMessageTypes"] = self.message_types
            self._logger.info("Filtering for message types: %s", self.message_types)

        self._logger.debug("Subscribe message: %s", subscribe_message)

        while True:
            try:
                async with websockets.connect(websocket_url) as websocket:
                    self._logger.info("Connected to AISStream.io websocket")

                    # Send subscription message
                    subscribe_message_json = json.dumps(subscribe_message)
                    await websocket.send(subscribe_message_json)
                    self._logger.info("Sent subscription message to AISStream.io")

                    # Process incoming messages
                    async for message_json in websocket:
                        await self._handle_message(message_json)

            except Exception as exc:
                self._logger.error("Error in AISStream connection: %s", exc)
                self._logger.info("Reconnecting in 5 seconds...")
                await asyncio.sleep(5)

    async def _handle_message(self, message_json: str) -> None:
        """Handle a message from AISStream.io.

        Parameters
        ----------
        message_json : str
            JSON string containing the message
        """
        try:
            message = json.loads(message_json)
            message_type = message.get("MessageType")

            self._logger.debug("Received message of type: %s", message_type)

            # Periodically print registry contents
            current_time = int(time.time())
            if current_time - self.last_registry_print > self.registry_print_interval:
                self.registry.print_registry(10)  # Print up to 10 vessels
                self.last_registry_print = current_time

            if not message_type or "Message" not in message:
                self._logger.debug("Skipping message with no type or content")
                return

            # Extract the AIS message based on its type
            ais_message = message["Message"].get(message_type)
            if not ais_message:
                self._logger.debug(
                    "Could not extract message content for type: %s",
                    message_type)
                return

            # Check if there's metadata available with additional vessel info
            if "MetaData" in message and message["MetaData"]:
                # Try to extract vessel name from metadata
                mmsi = str(ais_message.get("UserID", ""))
                if mmsi:
                    metadata = message["MetaData"]
                    # Check for ship name in various potential fields
                    ship_name = ""
                    if metadata.get("ShipName", "").strip():
                        ship_name = metadata.get("ShipName", "").strip()
                    elif metadata.get("Name", "").strip():
                        ship_name = metadata.get("Name", "").strip()
                    elif metadata.get("VesselName", "").strip():
                        ship_name = metadata.get("VesselName", "").strip()

                    if ship_name:
                        self._logger.info(
                            "Found ship name in MetaData: MMSI=%s, Name=%s",
                            mmsi,
                            ship_name,
                        )

                        # Update registry with this name
                        self.registry.update_vessel_static(
                            {"mmsi": mmsi, "name": ship_name, "source": "metadata"}
                        )

                    # Also check for callsign in metadata
                    callsign = metadata.get("CallSign", "").strip()
                    if callsign:
                        self._logger.debug(
                            "Found callsign in MetaData: MMSI=%s, CallSign=%s",
                            mmsi,
                            callsign,
                        )

            # For most message types, we need to transform to a format compatible with
            # our existing code
            transformed_message = self._transform_aisstream_message(
                ais_message, message_type
            )
            if not transformed_message:
                return

            # Process the message similar to how we handle other AIS sources
            await self._process_message(transformed_message)

        except json.JSONDecodeError:
            self._logger.error("Failed to decode JSON message: %s", message_json)
        except Exception as exc:
            self._logger.error("Error processing message: %s", exc)

    def _transform_aisstream_message(
        self, ais_message: Dict[str, Any], message_type: str
    ) -> Optional[Dict[str, Any]]:
        """Transform an AISStream.io message to our internal format.

        Parameters
        ----------
        ais_message : Dict[str, Any]
            The AIS message content
        message_type : str
            The type of AIS message

        Returns
        -------
        Optional[Dict[str, Any]]
            Transformed message in our internal format, or None if not applicable
        """
        # Create a compatible message format
        result = {}

        # Common fields
        mmsi = ais_message.get("UserID", "")
        result["mmsi"] = mmsi

        # Pre-filter messages without required fields to avoid error logs
        if not mmsi:
            self._logger.debug("Skipping message with no MMSI")
            return None

        # Extract name from any message type if present
        if "Name" in ais_message and ais_message["Name"]:
            vessel_name = ais_message["Name"].strip()
            if vessel_name:
                result["name"] = vessel_name
                # Update registry with this name
                self.registry.update_vessel_static(
                    {"mmsi": mmsi, "name": vessel_name, "source": f"{message_type}"}
                )
                self._logger.debug(
                    "Found vessel name in %s: MMSI=%s, Name=%s",
                    message_type,
                    mmsi,
                    vessel_name,
                )

        # Handle ShipName as a separate field if present (to match core
        # application's expectations)
        if "ShipName" in ais_message and ais_message["ShipName"]:
            shipname = ais_message["ShipName"].strip()
            if shipname:
                # Only add as separate field if different from name
                if "name" not in result or shipname != result["name"]:
                    result["shipname"] = shipname
                    self._logger.debug(
                        "Found different shipname: MMSI=%s, Shipname=%s", mmsi, shipname
                    )

        # Add fields specific to message types
        if message_type == "PositionReport":
            lat = ais_message.get("Latitude")
            lon = ais_message.get("Longitude")

            # Pre-filter messages without position data
            if not lat or not lon:
                self._logger.debug("Skipping PositionReport with missing lat/lon")
                return None

            result["lat"] = lat
            result["lon"] = lon

            # Store Course Over Ground - standardize on lowercase "cog" as that's what
            # our cot generator expects
            if "Cog" in ais_message and ais_message["Cog"] is not None:
                cog = float(ais_message["Cog"])
                result["cog"] = cog
                self._logger.debug("COG from PositionReport: %s", cog)

            # Store Speed Over Ground - standardize on uppercase SOG as that's what
            # our cot generator expects
            if "Sog" in ais_message and ais_message["Sog"] is not None:
                sog = float(ais_message["Sog"])
                result["SOG"] = sog
                self._logger.debug("SOG from PositionReport: %s", sog)

            # Get True Heading from message, standardize on lowercase "heading"
            if "TrueHeading" in ais_message:
                true_heading = ais_message.get("TrueHeading")
                # In AIS, 511 (0x1FF) means "not available"
                if true_heading == 511:
                    self._logger.debug("TrueHeading is 511 (not available)")
                    # If true heading is not available but we have COG, use that instead
                    if "Cog" in ais_message and ais_message["Cog"] is not None:
                        result["heading"] = float(ais_message["Cog"])
                        self._logger.debug(
                            "Using COG as heading since TrueHeading not available"
                        )
                else:
                    result["heading"] = float(true_heading)
                    self._logger.debug(
                        "TrueHeading from PositionReport: %s", true_heading)

            result["nav_status"] = ais_message.get("NavigationalStatus", 0)

            # Enrich message with vessel information from registry
            result = self.registry.enrich_message(result)

        elif message_type == "ShipStaticData":
            # For ShipStaticData, we don't need position, just update the registry
            result["name"] = ais_message.get("Name", "").strip()

            # Handle ShipName separately if it exists and differs from Name
            if "ShipName" in ais_message and ais_message["ShipName"]:
                shipname = ais_message["ShipName"].strip()
                if shipname and shipname != result.get("name", ""):
                    result["shipname"] = shipname

            result["shiptype"] = ais_message.get("ShipType", 0)
            result["callsign"] = ais_message.get("CallSign", "").strip()
            result["destination"] = ais_message.get("Destination", "").strip()
            result["eta"] = ais_message.get("Eta", "")
            result["dim_a"] = ais_message.get("DimensionToBow", 0)
            result["dim_b"] = ais_message.get("DimensionToStern", 0)
            result["dim_c"] = ais_message.get("DimensionToPort", 0)
            result["dim_d"] = ais_message.get("DimensionToStarboard", 0)

            # Debug log raw ship data
            self._logger.debug(
                "ShipStaticData raw: MMSI=%s, Name='%s', CallSign='%s', Eta=%s",
                ais_message.get("UserID", ""),
                ais_message.get("Name", ""),
                ais_message.get("CallSign", ""),
                ais_message.get("Eta", ""),
            )

            # Update vessel registry with static data
            self.registry.update_vessel_static(result)

            # Return None for ShipStaticData since we don't want to generate a CoT event
            # We just want to update the registry
            return None

        elif message_type == "StandardClassBPositionReport":
            lat = ais_message.get("Latitude")
            lon = ais_message.get("Longitude")

            # Pre-filter messages without position data
            if not lat or not lon:
                self._logger.debug(
                    "Skipping StandardClassBPositionReport with missing lat/lon")
                return None

            result["lat"] = lat
            result["lon"] = lon

            # Store Course Over Ground - standardize on lowercase "cog"
            if "Cog" in ais_message and ais_message["Cog"] is not None:
                cog = float(ais_message["Cog"])
                result["cog"] = cog
                self._logger.debug("COG from StandardClassBPositionReport: %s", cog)

            # Store Speed Over Ground - standardize on uppercase SOG
            if "Sog" in ais_message and ais_message["Sog"] is not None:
                sog = float(ais_message["Sog"])
                result["SOG"] = sog
                self._logger.debug("SOG from StandardClassBPositionReport: %s", sog)

            # Get True Heading from message
            if "TrueHeading" in ais_message:
                true_heading = ais_message.get("TrueHeading")
                # In AIS, 511 (0x1FF) means "not available"
                if true_heading == 511:
                    self._logger.debug("TrueHeading is 511 (not available)")
                    # If true heading is not available but we have COG, use that instead
                    if "Cog" in ais_message and ais_message["Cog"] is not None:
                        result["heading"] = float(ais_message["Cog"])
                        self._logger.debug(
                            "Using COG as heading since TrueHeading not available"
                        )
                else:
                    result["heading"] = float(true_heading)
                    self._logger.debug(
                        "TrueHeading from StandardClassBPositionReport: %s",
                        true_heading,
                    )

            # Enrich message with vessel information from registry
            result = self.registry.enrich_message(result)

        elif message_type == "ExtendedClassBPositionReport":
            lat = ais_message.get("Latitude")
            lon = ais_message.get("Longitude")

            # Pre-filter messages without position data
            if not lat or not lon:
                self._logger.debug(
                    "Skipping ExtendedClassBPositionReport with missing lat/lon")
                return None

            result["lat"] = lat
            result["lon"] = lon

            # Store Course Over Ground - standardize on lowercase "cog"
            if "Cog" in ais_message and ais_message["Cog"] is not None:
                cog = float(ais_message["Cog"])
                result["cog"] = cog
                self._logger.debug("COG from ExtendedClassBPositionReport: %s", cog)

            # Store Speed Over Ground - standardize on uppercase SOG
            if "Sog" in ais_message and ais_message["Sog"] is not None:
                sog = float(ais_message["Sog"])
                result["SOG"] = sog
                self._logger.debug("SOG from ExtendedClassBPositionReport: %s", sog)

            # Get True Heading from message
            if "TrueHeading" in ais_message:
                true_heading = ais_message.get("TrueHeading")
                # In AIS, 511 (0x1FF) means "not available"
                if true_heading == 511:
                    self._logger.debug("TrueHeading is 511 (not available)")
                    # If true heading is not available but we have COG, use that instead
                    if "Cog" in ais_message and ais_message["Cog"] is not None:
                        result["heading"] = float(ais_message["Cog"])
                        self._logger.debug(
                            "Using COG as heading since TrueHeading not available"
                        )
                else:
                    result["heading"] = float(true_heading)
                    self._logger.debug(
                        "TrueHeading from ExtendedClassBPositionReport: %s",
                        true_heading,
                    )

            # Enrich message with vessel information from registry
            result = self.registry.enrich_message(result)

        else:
            # For other message types, we may need to implement specific transformations
            self._logger.debug("Unsupported message type: %s", message_type)
            return None

        return result

    async def _process_message(self, msg: Dict[str, Any]) -> None:
        """Process a transformed AIS message.

        Parameters
        ----------
        msg : Dict[str, Any]
            Transformed message in our internal format
        """
        mmsi = str(msg.get("mmsi", ""))
        if not mmsi:
            return

        # Normalize the message data before sending to ais_to_cot function
        normalized_msg = self._normalize_ais_data(msg)
        self._logger.debug("Normalized data: %s", normalized_msg)

        # Check if this is a known craft
        known_craft: dict = {}
        if self.known_craft_db:
            matching_craft = list(filter(
                lambda x: x["MMSI"].strip().upper() == mmsi,
                self.known_craft_db,
            ))
            known_craft = matching_craft[0] if matching_craft else {}
            self._logger.debug("known_craft='%s'", known_craft)

        # Skip if we're using known_craft CSV and this Craft isn't found
        if self.known_craft_db:
            if not known_craft:
                if not self.config.getboolean("INCLUDE_ALL_CRAFT", False):
                    return

        # Convert to CoT XML
        event: Optional[bytes] = aiscot.cot_to_xml(
            normalized_msg, self.config, known_craft=known_craft
        )

        if event:
            self._logger.debug("Adding CoT event to queue: %s", event)
            await self._put_queue(event)

    def _normalize_ais_data(self, msg: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize AIS data to ensure consistent format for ais_to_cot function.

        Parameters
        ----------
        msg : Dict[str, Any]
            Original message

        Returns
        -------
        Dict[str, Any]
            Normalized message
        """
        normalized = msg.copy()

        # Ensure heading is properly handled
        if "heading" in normalized:
            try:
                heading_val = float(normalized["heading"])
                # In AIS, 511 (0x1FF) means "not available"
                if heading_val == 511 or heading_val < 0 or heading_val > 360:
                    # If heading is invalid but we have COG (Course Over Ground), use
                    # that instead
                    if "cog" in normalized and normalized["cog"] is not None:
                        try:
                            cog_val = float(normalized["cog"])
                            if 0 <= cog_val <= 360:
                                self._logger.debug("Using COG %s for heading", cog_val)
                                normalized["heading"] = cog_val
                            else:
                                # Invalid COG, remove heading
                                normalized.pop("heading", None)
                        except (ValueError, TypeError):
                            # Invalid COG, remove heading
                            normalized.pop("heading", None)
                    else:
                        # No valid COG, remove heading
                        normalized.pop("heading", None)
            except (ValueError, TypeError):
                # If heading can't be converted to float, remove it
                normalized.pop("heading", None)

        # Ensure Course Over Ground (cog) is properly formatted
        if "cog" in normalized:
            try:
                cog_val = float(normalized["cog"])
                if 0 <= cog_val <= 360:
                    normalized["cog"] = cog_val
                else:
                    normalized.pop("cog", None)
            except (ValueError, TypeError):
                normalized.pop("cog", None)

        # Ensure speed (SOG) is properly formatted
        # NOTE: The ais_to_cot function expects speed in 0.1-knot units
        # and converts with:
        # sog = float(sog) * 0.1 / 1.944
        # But AISStream.io provides speeds directly in knots, so we need to
        # multiply by 10 to compensate for the 0.1 multiplication in ais_to_cot
        if "SOG" in normalized:
            try:
                # Multiply by 10 to convert from knots to 0.1-knot units expected by
                # ais_to_cot
                sog_knots = float(normalized["SOG"])
                sog_adjusted = sog_knots * 10
                normalized["SOG"] = sog_adjusted
                self._logger.debug(
                    "Adjusted SOG from %s knots to %s (0.1-knot units)",
                    sog_knots,
                    sog_adjusted,
                )
            except (ValueError, TypeError):
                normalized.pop("SOG", None)

        # Ensure lat/lon are valid floats
        for coord in ["lat", "lon"]:
            if coord in normalized:
                try:
                    coord_val = float(normalized[coord])
                    normalized[coord] = coord_val
                except (ValueError, TypeError):
                    # If coordinate can't be converted to float, this message will be
                    # skipped later
                    normalized.pop(coord, None)

        # Ensure MMSI is a string
        if "mmsi" in normalized:
            normalized["mmsi"] = str(normalized["mmsi"])

        # Ensure name is a clean string
        if "name" in normalized and normalized["name"]:
            normalized["name"] = str(normalized["name"]).strip()

        return normalized

    async def _put_queue(self, event: bytes) -> None:
        """Put event on queue for processing.

        Parameters
        ----------
        event : bytes
            CoT event to put on queue
        """
        await self.queue.put(event)
