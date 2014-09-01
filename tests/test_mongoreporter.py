# -*- coding: utf-8 -*-
"""Unit tests for mongodog MongoReporter
It's a little bit of a special case, because we don't want it to start reporting its own commands"""
try:
    # if pymongo available
    import pymongo
    PYMONGO_AVAILABLE = True
except ImportError:
    PYMONGO_AVAILABLE = False

import mongodog.reporters
import mongodog.sniffer
from mongoboxed import BaseMongoBoxedTestCase


class TestSnifferWithMongoReporter(BaseMongoBoxedTestCase):
    """Unit tests for MongoReporter class"""

    def setUp(self):
        self.client = self.mongobox.client()
        self.db = self.client.mongodog_test
        self.reporter = mongodog.reporters.MongoReporter(self.db.mongodog_commands)
        self.sniffer = mongodog.sniffer.Sniffer(self.reporter)

    def tearDown(self):
        self.sniffer.stop()
        for collection in self.client.mongodog_test.collection_names():
            if collection not in ('system.indexes',):
                self.client.mongodog_test[collection].drop()

    def test_ignores_own_commands(self):
        """MongoReporter ignores own commands (inserts)"""
        self.sniffer.start()
        self.db.foo.insert({'this_is': 'foo'})

        self.assertEqual(1, self.db.mongodog_commands.find({'op': 'collection_insert'}).count())

    def test_make_sure_it_all_works(self):
        """You can log all sorts of commands, and it all works fine"""
        self.sniffer.start()
        self.db.foo.insert([{'this_is': 'foo', 'num': i} for i in range(10)])
        doc4 = self.db.foo.find_one({'num': 4})
        self.db.foo.remove(doc4['_id'])
        self.db.foo.update({'num': {'$gt': 2, '$lt': 5}}, {'$set': {'this_is': 'updated'}})
        self.assertEqual(9, self.db.foo.count())
