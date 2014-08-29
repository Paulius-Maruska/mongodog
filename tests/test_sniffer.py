# -*- coding: utf-8 -*-
"""
Unit tests for MongoDog
"""
import unittest

import mongodog.reporters
import mongodog.sniffer


class TestMongodogSnifferDecorator(unittest.TestCase):
    """Unit tests for mongodog_sniffer decorator"""

    def test_decorator_calls_original_function(self):
        """decorator calls original function and passes the correct arguments"""
        calls = []
        @mongodog.sniffer.mongodog_sniffer()
        def dummy(*args, **kwargs):
            calls.append({'args': args, 'kwargs': kwargs})
            return 1337

        r = dummy(1, 2, a=3, b=4)

        self.assertEqual(1, len(calls))
        self.assertEqual({'args': (1, 2), 'kwargs': {'a': 3, 'b': 4}}, calls[0])
        self.assertEqual(1337, r)

    def test_decorator_calls_callback_before_before_calling_function(self):
        """decorator calls callback_before, before calling original function"""
        calls = []

        def before(custom, *args, **kwargs):
            calls.append({'f': 'before', 'c': custom, 'args': args, 'kwargs': kwargs})

        @mongodog.sniffer.mongodog_sniffer(callback_before=before)
        def dummy(*args, **kwargs):
            calls.append({'f': 'dummy', 'args': args, 'kwargs': kwargs})

        dummy(1, a=2)

        self.assertEqual(2, len(calls))
        self.assertEqual({'f': 'before', 'c': None, 'args': (1,), 'kwargs': {'a': 2}}, calls[0])
        self.assertEqual({'f': 'dummy', 'args': (1,), 'kwargs': {'a': 2}}, calls[1])

    def test_decorator_calls_callback_before_and_skips_function_call_if_skipcall_raised(self):
        """decorator calls callback_before and skips calling original function if SkipCall raised"""
        calls = []

        def before(custom, *args, **kwargs):
            calls.append({'f': 'before', 'c': custom, 'args': args, 'kwargs': kwargs})
            raise mongodog.sniffer.SkipCall()

        @mongodog.sniffer.mongodog_sniffer(callback_before=before)
        def dummy(*args, **kwargs):
            calls.append({'f': 'dummy', 'args': args, 'kwargs': kwargs})

        dummy(1, a=2)

        self.assertEqual(1, len(calls))
        self.assertEqual({'f': 'before', 'c': None, 'args': (1,), 'kwargs': {'a': 2}}, calls[0])

    def test_decorator_calls_callback_after_after_calling_function(self):
        """decorator calls function and then calls callback_after"""
        calls = []

        def after(result, custom, *args, **kwargs):
            calls.append({'f': 'after', 'r': result, 'c': custom, 'args': args, 'kwargs': kwargs})

        @mongodog.sniffer.mongodog_sniffer(callback_after=after)
        def dummy(*args, **kwargs):
            calls.append({'f': 'dummy', 'args': args, 'kwargs': kwargs})
            return 31373

        result = dummy(1, a=2)

        self.assertEqual(2, len(calls))
        self.assertEqual({'f': 'dummy', 'args': (1,), 'kwargs': {'a': 2}}, calls[0])
        self.assertEqual({'f': 'after', 'r': 31373, 'c': None, 'args': (1,), 'kwargs': {'a': 2}}, calls[1])
        self.assertEqual(31373, result)


class TestSniffer(unittest.TestCase):
    """Unit tests for the Sniffer class"""

    def dummy(self, *args, **kwargs):
        self.calls.append(('dummy', args, kwargs))
        return self.return_value

    def setUp(self):
        super(TestSniffer, self).setUp()
        self.calls = []
        self.return_value = None
        self.original_sniffer_config = mongodog.sniffer.Sniffer.config
        mongodog.sniffer.Sniffer.config = [('dummy', TestSniffer, 'dummy')]

    def tearDown(self):
        super(TestSniffer, self).tearDown()
        mongodog.sniffer.Sniffer.config = self.original_sniffer_config

    def test_constructor_correctly_initializes_structures_from_config(self):
        """Sniffer constructor correctly initializes `original` and `decorated`"""
        reporter = mongodog.reporters.MemoryReporter()
        sniffer = mongodog.sniffer.Sniffer(reporter)

        dummypath = '%s.%s.%s' % (TestSniffer.__module__, TestSniffer.__name__, 'dummy')
        self.assertIn(dummypath, sniffer.original)
        self.assertIn(dummypath, sniffer.decorated)

    def test_sniffer_reports_all_function_calls_between_start_and_stuff(self):
        """Sniffer reports all calls of the original function, in between `start` and `stop` calls"""
        reporter = mongodog.reporters.MemoryReporter()
        sniffer = mongodog.sniffer.Sniffer(reporter, False)

        self.return_value = 1
        self.assertEqual(1, self.dummy(1))
        sniffer.start()
        self.return_value = 2
        self.assertEqual(2, self.dummy(2))
        sniffer.stop()
        self.return_value = 3
        self.assertEqual(3, self.dummy(3))

        self.assertEqual([('dummy', (1,), {}), ('dummy', (2,), {}), ('dummy', (3,), {})], self.calls)
        self.assertEqual([({'op': 'dummy', 'args': (2,), 'kwargs': {}}, None)], reporter.reported_commands)
