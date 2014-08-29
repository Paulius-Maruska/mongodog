# -*- coding: utf-8 -*-
"""
Integration with mongokit tests
"""
import unittest
import time

try:
    import mongokit
    from mongokit import Document
    MONGOKIT_INSTALLED = True
except ImportError:
    class Document(object):
        """dummy class, to make it compile without mongokit"""
        pass
    MONGOKIT_INSTALLED = False

from test_pymongo import TestMongoDogWithPyMongo


@unittest.skipUnless(MONGOKIT_INSTALLED, "Not running MongoKit integration tests, if there is no MongoKit installed")
class TestMongoDogWithMongoKit(TestMongoDogWithPyMongo):
    """Integration tests for mongodog and mongokit"""

    class DummyDocument(Document):
        """Dummy document definition"""
        __database__ = 'mongodog_test'
        __collection__ = 'dummy_documents'
        structure = {'a': int, 'b': int}

    def setUp(self):
        super(TestMongoDogWithMongoKit, self).setUp()
        # init mongo client
        self.client = mongokit.MongoClient(port=self.mongobox.port)
        self.client.register([self.DummyDocument])

    def test_sniffer_reports_document_save_as_collection_save(self):
        """Sniffer reports document save as collection save"""
        doc = self.client.DummyDocument()
        doc.update({'a': 1, 'b': 2})

        self.sniffer.start()
        doc.save()
        self.assertLess(0, len(self.reporter.reported_commands))

        command = None
        for cmd in self.reporter.reported_commands:
            if cmd[0]['op'] == 'collection_save':
                command = cmd[0]
                break
        self.assertIsNotNone(command, "`collection_save` command not reported")
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('dummy_documents', command['collection'])
        self.assertEqual('collection_save', command['op'])
        self.assertEqual({'a': 1, 'b': 2}, command['to_save'])

    def test_sniffer_reports_delete_called_on_document_class(self):
        """Sniffer reports collection remove calls, when they are called on a document class"""
        for i in range(10):
            doc = self.client.DummyDocument()
            doc.update({'a': i % 2, 'b': i})
            doc.save(w=1)

        doc = self.client.DummyDocument.find({'b': 4})[0]
        # workaround for some weird mongokit error
        doc2 = self.client.DummyDocument()
        doc2.update(doc)

        self.sniffer.start()
        doc2.delete()
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('dummy_documents', command['collection'])
        self.assertEqual('collection_remove', command['op'])
        self.assertEqual({'_id': doc['_id']}, command['spec_or_id'])

    def test_sniffer_reports_find_called_on_document_class(self):
        """Sniffer reports collection find calls, when they are called on a document class"""
        for i in range(10):
            doc = self.client.DummyDocument()
            doc.update({'a': i % 2, 'b': i})
            doc.save()

        self.sniffer.start()
        _result = self.client.DummyDocument.find({'b': 4})
        self.assertLess(0, len(self.reporter.reported_commands))

        command = self.reporter.reported_commands[0][0]
        self.assertEqual('mongodog_test', command['db'])
        self.assertEqual('dummy_documents', command['collection'])
        self.assertEqual('collection_find', command['op'])
        self.assertEqual({'b': 4}, command['spec'])
