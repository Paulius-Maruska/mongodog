# -*- coding: utf-8 -*-
"""Unit tests for mongodog reporters"""
try:
    # python2
    import StringIO as io
except ImportError:
    # python3
    import io
import logging
import unittest

try:
    # if pymongo available
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

import mongodog.reporters
import mongodog.utils
from mongoboxed import BaseMongoBoxedTestCase


class TestBaseReporter(unittest.TestCase):
    """Unit tests for BaseReporter class"""

    def test_report_mongo_command_raises_not_implemented_error(self):
        """BaseReporter.report_mongo_command raises NotImplementedException"""
        reporter = mongodog.reporters.BaseReporter()

        self.assertRaises(NotImplementedError, reporter.report_mongo_command, {})


class TestMemoryReporter(unittest.TestCase):
    """Unit tests for MemoryReporter class"""

    def test_collects_reported_commands(self):
        """MemoryReporter should store all commands in `reported_commands` list"""
        reporter = mongodog.reporters.MemoryReporter()
        reporter.report_mongo_command({"cmd": 1})
        reporter.report_mongo_command({"cmd": 2})
        self.assertEqual([({"cmd": 1}, None), ({"cmd": 2}, None)], reporter.reported_commands)


class TestLoggingReporter(unittest.TestCase):
    """Unit tests for LoggingReporter class"""

    def test_raises_value_error_when_trying_to_pass_nonsense_to_constructor(self):
        """LoggingReporter raises ValueError exception, when constructor is not supplied with either
        a logging.Logger or str object (logger name)."""
        self.assertRaises(ValueError, mongodog.reporters.LoggingReporter, None)
        self.assertRaises(ValueError, mongodog.reporters.LoggingReporter, 1)
        self.assertRaises(ValueError, mongodog.reporters.LoggingReporter, 1.5)
        self.assertRaises(ValueError, mongodog.reporters.LoggingReporter, [])
        self.assertRaises(ValueError, mongodog.reporters.LoggingReporter, {})

    def test_uses_supplied_logger(self):
        """LoggingReporter uses logger object supplied to the constructor"""
        lbuf = io.StringIO()
        logger = logging.getLogger("mongodog.tests.dummy.1")
        logger.handlers = []
        logger.addHandler(logging.StreamHandler(lbuf))
        logger.propagate = False

        reporter = mongodog.reporters.LoggingReporter(logger)
        reporter.report_mongo_command({"dummy_mongo_command": 1})

        content = lbuf.getvalue()

        self.assertTrue(content.find("mongodog:") != -1)
        self.assertTrue(content.find("dummy_mongo_command") != -1)

    def test_obtains_specified_logger_by_name(self):
        """LoggingReporter obtains correct logger when suplied logger name to the constructor"""
        lbuf = io.StringIO()
        logger = logging.getLogger("mongodog.tests.dummy.2")
        logger.handlers = []
        logger.addHandler(logging.StreamHandler(lbuf))
        logger.propagate = False

        reporter = mongodog.reporters.LoggingReporter("mongodog.tests.dummy.2")
        reporter.report_mongo_command({"dummy_mongo_command": 1})

        content = lbuf.getvalue()

        self.assertTrue(content.find("mongodog:") != -1)
        self.assertTrue(content.find("dummy_mongo_command") != -1)

    def test_includes_traceback_in_log_when_supplied(self):
        """LoggingReporter outputs the log, when it is provided"""
        def dummy_traceback_marker():
            return mongodog.utils.get_full_traceback()

        lbuf = io.StringIO()
        logger = logging.getLogger("mongodog.tests.dummy.3")
        logger.handlers = []
        logger.addHandler(logging.StreamHandler(lbuf))
        logger.propagate = False

        reporter = mongodog.reporters.LoggingReporter(logger)
        reporter.report_mongo_command({"dummy_mongo_command": 1}, dummy_traceback_marker())

        content = lbuf.getvalue()

        self.assertTrue(content.find("dummy_traceback_marker") != -1)


class TestMongoReporter(BaseMongoBoxedTestCase):
    """Unit tests for MongoReporter class"""

    def setUp(self):
        # init mongo client
        self.client = self.mongobox.client()

    def tearDown(self):
        # drop all collections
        for collection in self.client.mongodog_test.collection_names():
            if collection not in ('system.indexes',):
                self.client.mongodog_test[collection].drop()

    def test_commands_are_inserted_into_configured_collection(self):
        """MongoReporter inserts commands into the configured collection"""
        db = self.client.mongodog_test
        reporter = mongodog.reporters.MongoReporter(db.mongodog_reports)
        reporter.report_mongo_command({"db": "mongodog_test", "collection": "foo", "op": "unknown"})

        self.assertEqual(1, len(list(db.mongodog_reports.find())))

    def test_reported_commands_include_traceback(self):
        """MongoReporter does not report own commands (inserts)"""
        db = self.client.mongodog_test
        reporter = mongodog.reporters.MongoReporter(db.mongodog_reports)
        cmd = {"db": "mongodog_test", "collection": "foo", "op": "unknown"}
        tb = mongodog.utils.get_full_traceback()
        reporter.report_mongo_command(cmd, tb)

        doc = db.mongodog_reports.find_one()
        self.assertIn("_traceback", doc)
        self.assertIsInstance(doc['_traceback'], list)
        self.assertLess(0, len(doc['_traceback']))
