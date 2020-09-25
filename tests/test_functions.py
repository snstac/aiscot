#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""AIS Cursor-on-Target Gateway Function Tests."""

import unittest

import aiscot.functions

__author__ = 'Greg Albrecht W2GMD <oss@undef.net>'
__copyright__ = 'Copyright 2020 Orion Labs, Inc.'
__license__ = 'Apache License, Version 2.0'


class FunctionsTestCase(unittest.TestCase):
    """
    Test class for functions... functions.
    """

    def test_ais_to_cot(self):
        """
        Tests that ais_to_cot decodes an AIS Sentence into a Cursor-on-Target
        message.
        """
        test_sentence = {
            'id': 1,
            'repeat_indicator': 0,
            'mmsi': 211433000,
            'nav_status': 0,
            'rot_over_range': True,
            'rot': -731.386474609375,
            'sog': 1.100000023841858,
            'position_accuracy': 1,
            'x': -122.65529333333333,
            'y': 37.72890666666667,
            'cog': 80.30000305175781,
            'true_heading': 511,
            'timestamp': 25,
            'special_manoeuvre': 0,
            'spare': 0,
            'raim': True,
            'sync_state': 0,
            'slot_timeout': 3,
            'received_stations': 133,
            'nmea': '!AIVDM,1,1,,B,139`n:0P0;o>Qm@EUc838wvj2<25,0*4E\n'
        }
        cot_msg = aiscot.functions.ais_to_cot(test_sentence)
        self.assertEqual(cot_msg.event_type, 'a-f-G-E-V-C')
        self.assertEqual(cot_msg.uid, 'AIS.211433000')


if __name__ == '__main__':
    unittest.main()
