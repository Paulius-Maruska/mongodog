# -*- coding: utf-8 -*-
"""Unit tests for the helper functions"""
import unittest
import traceback

import mongodog.utils


class TestGetTraceback(unittest.TestCase):
    """Tests for the function get_traceback"""

    def test_last_frame_in_traceback_is_get_traceback_itself(self):
        """By default, last frame in the traceback is the get_traceback function itself"""
        tb = traceback.extract_tb(mongodog.utils.get_full_traceback())
        self.assertIsInstance(tb, list)
        self.assertLess(0, len(tb))

        last_frame = tb[-1]
        self.assertTrue(last_frame[2].find("get_traceback") != -1)

    def test_top_frames_can_be_skipped_with_function_parameter(self):
        """Requested amount of last frames should be omitted from the traceback"""

        def dummy_wrapper(skip=1):
            """wrapper (the last frame)"""
            return traceback.extract_tb(mongodog.utils.get_full_traceback(skip))

        tb = dummy_wrapper()
        self.assertIsInstance(tb, list)
        self.assertLess(0, len(tb))

        last_frame = tb[-1]
        self.assertTrue(last_frame[3].find("dummy_wrapper()") != -1)
