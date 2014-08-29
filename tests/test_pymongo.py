# -*- coding: utf-8 -*-
"""
Integration with pymongo tests
"""
import bson
import mongobox

import mongodog
from integration import BaseIntegrationTestCase


class TestMongoDogWithPyMongo(BaseIntegrationTestCase):
    """Integration tests for mongodog and pymongo"""

    def setUp(self):
        # create mongodog sniffer
        self.reporter = mongodog.MemoryReporter()
        self.sniffer = mongodog.Sniffer(self.reporter)
        # init mongo client
        self.client = self.mongobox.client()

    def tearDown(self):
        # stop sniffing
        self.sniffer.stop()
        # drop all collections
        for collection in self.client.mongodog_test.collection_names():
            if collection not in ('system.indexes',):
                self.client.mongodog_test[collection].drop()

    def test_sniffer_reports_database_command(self):
        """Sniffer reports database command calls"""
        db = self.client.mongodog_test

        self.sniffer.start()
        _result = db.command("buildinfo")
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('database_command', command['op'])
        self.assertEqual('buildinfo', command['command'])
        self.assertEqual(1, command['value'])

    def test_sniffer_reports_collection_aggregate(self):
        """Sniffer reports collection aggregate calls"""
        db = self.client.mongodog_test
        db.aggregate_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        _result = db.aggregate_test.aggregate([{'$group': {'_id': '$a', 's': {'$sum': '$b'}}}])
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('aggregate_test', command['collection'])
        self.assertEqual('collection_aggregate', command['op'])
        self.assertEqual([{'$group': {'_id': '$a', 's': {'$sum': '$b'}}}], command['pipeline'])

    def test_sniffer_reports_collection_count(self):
        """Sniffer reports collection count calls"""
        db = self.client.mongodog_test
        db.count_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        _result = db.count_test.count()
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('count_test', command['collection'])
        self.assertEqual('collection_count', command['op'])

    def test_sniffer_reports_collection_distinct(self):
        """Sniffer reports collection count calls"""
        db = self.client.mongodog_test
        db.distinct_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        _result = db.distinct_test.distinct('a')
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('distinct_test', command['collection'])
        self.assertEqual('collection_distinct', command['op'])
        self.assertEqual('a', command['key'])

    def test_sniffer_reports_collection_find(self):
        """Sniffer reports collection find calls"""
        db = self.client.mongodog_test
        db.find_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        _result = db.find_test.find({'a': 0}, sort=[('b', -1)], skip=1, limit=2)
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('find_test', command['collection'])
        self.assertEqual('collection_find', command['op'])
        self.assertEqual({'a': 0}, command['spec'])
        self.assertIsNone(command['fields'])
        self.assertEqual(1, command['skip'])
        self.assertEqual(2, command['limit'])
        self.assertEqual([('b', -1)], command['sort'])

    def test_sniffer_reports_collection_find_and_modify(self):
        """Sniffer reports collection find_and_modify calls"""
        db = self.client.mongodog_test
        db.find_and_modify_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        _result = db.find_and_modify_test.find_and_modify(
            {'a': 1}, {'$set': {'c': 'foo'}}, sort=[('b', 1)])
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('find_and_modify_test', command['collection'])
        self.assertEqual('collection_find_and_modify', command['op'])
        self.assertEqual({'a': 1}, command['query'])
        self.assertEqual({'$set': {'c': 'foo'}}, command['update'])
        self.assertEqual(False, command['upsert'])
        self.assertEqual([('b', 1)], command['sort'])

    def test_sniffer_reports_collection_find_one(self):
        """Sniffer reports collection find_one calls"""
        db = self.client.mongodog_test
        db.find_one_test.insert([{'a': x % 2, 'b': x} for x in range(10)])
        _id = db.find_one_test.find({'b': 3}).limit(1)[0]['_id']

        self.sniffer.start()
        _result = db.find_one_test.find_one(_id, {'_id': False, 'a': True})
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('find_one_test', command['collection'])
        self.assertEqual('collection_find_one', command['op'])
        self.assertEqual(_id, command['spec_or_id'])
        self.assertEqual({'_id': False, 'a': True}, command['fields'])

    def test_sniffer_reports_collection_group(self):
        """Sniffer reports collection group calls"""
        db = self.client.mongodog_test
        db.group_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        _result = db.group_test.group(
            {'a': 1}, {'b': {'$gt': 1}}, {'count': 0}, "function(obj, prev){prev.count++}"
        )
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('group_test', command['collection'])
        self.assertEqual('collection_group', command['op'])
        self.assertEqual({'a': 1}, command['key'])
        self.assertEqual({'b': {'$gt': 1}}, command['condition'])
        self.assertEqual({'count': 0}, command['initial'])
        self.assertEqual("function(obj, prev){prev.count++}", command['reduce'])

    def test_sniffer_reports_collection_inline_map_reduce(self):
        """Sniffer reports collection inline_map_reduce calls"""
        db = self.client.mongodog_test
        db.inline_map_reduce_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        fmap = "function(){emit(this.a, 1)}"
        freduce = "function(k,v){var s=0;for(var i=0;i<v.length;++i)s+=v[i];return s}"
        _result = db.inline_map_reduce_test.inline_map_reduce(fmap, freduce)
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('inline_map_reduce_test', command['collection'])
        self.assertEqual('collection_inline_map_reduce', command['op'])
        self.assertEqual(fmap, command['map'])
        self.assertEqual(freduce, command['reduce'])

    def test_sniffer_reports_collection_insert(self):
        """Sniffer reports collection insert calls"""
        db = self.client.mongodog_test

        self.sniffer.start()
        db.insert_test.insert([{'a': x % 2, 'b': x} for x in range(10)])
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('insert_test', command['collection'])
        self.assertEqual('collection_insert', command['op'])
        self.assertEqual([{'a': x % 2, 'b': x} for x in range(10)], command['doc_or_docs'])

    def test_sniffer_reports_collection_map_reduce(self):
        """Sniffer reports collection map_reduce calls"""
        db = self.client.mongodog_test
        db.map_reduce_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        fmap = "function(){emit(this.a, 1)}"
        freduce = "function(k,v){var s=0;for(var i=0;i<v.length;++i)s+=v[i];return s}"
        _result = db.map_reduce_test.map_reduce(fmap, freduce, "map_reduce_result")
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('map_reduce_test', command['collection'])
        self.assertEqual('collection_map_reduce', command['op'])
        self.assertEqual(fmap, command['map'])
        self.assertEqual(freduce, command['reduce'])
        self.assertEqual("map_reduce_result", command['out'])

    def test_sniffer_reports_collection_remove(self):
        """Sniffer reports collection remove calls"""
        db = self.client.mongodog_test
        db.remove_test.insert([{'a': x % 2, 'b': x} for x in range(10)])
        _id = db.remove_test.find({'b': 3}).limit(1)[0]['_id']

        self.sniffer.start()
        _result = db.remove_test.remove(_id)
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('remove_test', command['collection'])
        self.assertEqual('collection_remove', command['op'])
        self.assertEqual(_id, command['spec_or_id'])

    def test_sniffer_reports_collection_save(self):
        """Sniffer reports collection save calls"""
        db = self.client.mongodog_test
        db.save_test.insert([{'a': x % 2, 'b': x} for x in range(10)])
        doc = db.save_test.find_one({'b': 3})

        self.sniffer.start()
        doc['c'] = "foo"
        _result = db.save_test.save(doc)
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('save_test', command['collection'])
        self.assertEqual('collection_save', command['op'])
        self.assertEqual(doc, command['to_save'])

    def test_sniffer_reports_collection_update(self):
        """Sniffer reports collection update calls"""
        db = self.client.mongodog_test
        db.update_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        self.sniffer.start()
        _result = db.update_test.update({'b': 3}, {'$set': {'c': 'foo'}})
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('update_test', command['collection'])
        self.assertEqual('collection_update', command['op'])
        self.assertEqual({'b': 3}, command['spec'])
        self.assertEqual({'$set': {'c': 'foo'}}, command['document'])

    def test_sniffer_reports_cursor_iter(self):
        """Sniffer reports cursor __iter__ calls"""
        db = self.client.mongodog_test
        db.cursor_iter_test.insert([{'a': x % 2, 'b': x} for x in range(10)])

        cursor = db.cursor_iter_test.find({'a': 0}).sort([('b', -1)]).skip(1).limit(2)

        self.sniffer.start()
        _result = list(cursor)
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertIsNotNone(command, "`cursor_iter` command was not reported")
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('cursor_iter_test', command['collection'])
        self.assertEqual('cursor_iter', command['op'])
        self.assertEqual({'a': 0}, command['spec'])
        self.assertIsNone(command['fields'])
        self.assertEqual(1, command['skip'])
        self.assertEqual(2, command['limit'])
        self.assertEqual(bson.SON([('b', -1)]), command['ordering'])
