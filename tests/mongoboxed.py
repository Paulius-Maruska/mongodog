# -*- coding: utf-8 -*-
"""
Defines base class for integration tests
"""
import unittest

import mongobox


class BaseMongoBoxedTestCase(unittest.TestCase):
    """Base class for all integration tests - auto-starts mongobox"""

    @classmethod
    def setUpClass(cls):
        try:
            cls.mongobox = mongobox.MongoBox(scripting=True)
            cls.mongobox.start()
        except Exception as error:
            message = "Could not start MongoBox: %s" % error.message
            raise unittest.SkipTest(message)

    @classmethod
    def tearDownClass(cls):
        cls.mongobox.stop()
