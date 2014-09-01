# -*- coding: utf-8 -*-
"""
Defines the Sniffer
"""
import copy

import pymongo.collection
import pymongo.cursor
import pymongo.database

try:
    import mongokit.collection

    MONGOKIT_INSTALLED = True
except ImportError:
    MONGOKIT_INSTALLED = False
from bson.binary import OLD_UUID_SUBTYPE
from pymongo.read_preferences import ReadPreference

import mongodog.utils


class SkipCall(Exception):
    """Used by mongodog_sniffer to skip the call"""
    pass


def mongodog_sniffer(custom=None, callback_before=None, callback_after=None):
    """Returns a decorator, that can be used to wrap any function or method.

    :Parameters:
    - `custom`: any object, it will be passed to the callbacks as-is
    - `callback_before`: a function that accepts `custom` as the first
    positional argument followed by the rest of positional and keyword
    arguments used to call the decorated function. If this callback raises
    `SkipCall` exception the decorated function and `callback_after` will
    not get called and None will be returned.
    - `callback_after`: a function that accepts result of the original
    function and `custom` as the first two positional arguments followed
    by the rest of the positional and keyword arguments passed to the call.
    """

    def actual_decorator(func):
        """An actual decorator function"""

        def replacement(*args, **kwargs):
            """Calls `callback_before`, then calls `func` and finally calls
            `callback_after`.
            Returns whatever `func` returned."""
            result = None
            proceed = True
            try:
                if callback_before is not None:
                    callback_before(custom, *args, **kwargs)
            except SkipCall:
                proceed = False

            if proceed:
                result = func(*args, **kwargs)

                if callback_after is not None:
                    callback_after(result, custom, *args, **kwargs)

            return result

        return replacement

    return actual_decorator


SNIFFER_CONFIG = [
    # pymongo database methods
    ('database_command', pymongo.database.Database, 'command'),
    # pymongo collection methods
    ('collection_aggregate', pymongo.collection.Collection, 'aggregate'),
    ('collection_count', pymongo.collection.Collection, 'count'),
    ('collection_distinct', pymongo.collection.Collection, 'distinct'),
    ('collection_find', pymongo.collection.Collection, 'find'),
    ('collection_find_and_modify', pymongo.collection.Collection,
     'find_and_modify'),
    ('collection_find_one', pymongo.collection.Collection, 'find_one'),
    ('collection_group', pymongo.collection.Collection, 'group'),
    ('collection_inline_map_reduce', pymongo.collection.Collection,
     'inline_map_reduce'),
    ('collection_insert', pymongo.collection.Collection, 'insert'),
    ('collection_map_reduce', pymongo.collection.Collection, 'map_reduce'),
    ('collection_remove', pymongo.collection.Collection, 'remove'),
    ('collection_save', pymongo.collection.Collection, 'save'),
    ('collection_update', pymongo.collection.Collection, 'update'),
    # pymongo cursor methods
    ('cursor_iter', pymongo.cursor.Cursor, '__iter__'),
]

if MONGOKIT_INSTALLED:
    SNIFFER_CONFIG += [
        # mongokit overrides collection_find
        ('collection_find', mongokit.collection.Collection, 'find')
    ]


class Sniffer(object):
    """Main class that does all the sniffing of pymongo activity"""

    config = SNIFFER_CONFIG

    def __init__(self, reporter, with_traceback=True):
        self.reporter = reporter
        self.with_traceback = with_traceback
        self.last_op = None

        self.original = {}
        self.decorated = {}

        for func, cls, method in self.config:
            custom = {'f': func}
            callback_before = getattr(self, 'callback_before_%s' % func,
                                      self.callback_before_generic)
            callback_after = getattr(self, 'callback_after_%s' % func, None)
            original_function = getattr(cls, method)
            original_function_path = '%s.%s.%s' % (cls.__module__,
                                                   cls.__name__,
                                                   method)
            decorator = mongodog_sniffer(custom, callback_before,
                                         callback_after)

            self.original[original_function_path] = original_function
            self.decorated[original_function_path] = \
                decorator(original_function)

    def start(self):
        """Starts sniffing"""
        for _, cls, method in self.config:
            original_function_path = '%s.%s.%s' % (cls.__module__,
                                                   cls.__name__,
                                                   method)
            setattr(cls, method, self.decorated[original_function_path])

    def stop(self):
        """Stops sniffing"""
        for _, cls, method in self.config:
            original_function_path = '%s.%s.%s' % (cls.__module__,
                                                   cls.__name__,
                                                   method)
            setattr(cls, method, self.original[original_function_path])

    def report_command(self, command):
        """Reports command to the configured reporter"""
        traceback = None
        if self.with_traceback:
            traceback = mongodog.utils.get_full_traceback()
        # pymongo tends to modify some things within calls
        # let's make a copy
        command_copy = copy.deepcopy(command)
        self.reporter.report_mongo_command(command_copy, traceback)

    def callback_before_generic(self, custom, *args, **kwargs):
        """Generic callback for unrecognized functions"""
        args_to_report = args
        if len(args) > 0 and isinstance(args[0], object):
            args_to_report = args[1:]
        command = {
            'op': custom['f'],
            'args': args_to_report,
            'kwargs': kwargs,
        }
        self.report_command(command)

    def callback_before_database_command(
            self, custom, database, command, value=1, check=True,
            allowable_errors=[], uuid_subtype=OLD_UUID_SUBTYPE,
            compile_re=True, **kwargs):
        """Callback used with pymongo database command call"""
        cmd = {
            'db': database.name,
            'op': custom['f'],
            'command': command,
            'value': value,
            'check': check,
            'allowable_errors': allowable_errors,
            'uuid_subtype': uuid_subtype,
            'compile_re': compile_re,
        }
        cmd.update(kwargs)
        self.report_command(cmd)

    def callback_before_collection_aggregate(self, custom, collection,
                                             pipeline, **kwargs):
        """Callback used with pymongo collection aggregate call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'pipeline': pipeline,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_count(self, custom, collection):
        """Callback used with pymongo collection count call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
        }
        self.report_command(command)

    def callback_before_collection_distinct(self, custom, collection, key):
        """Callback used with pymongo collection distinct call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'key': key,
        }
        self.report_command(command)

    def callback_before_collection_find(
            self, custom, collection, spec=None, fields=None, skip=0, limit=0,
            timeout=True, snapshot=False, tailable=False, sort=None,
            max_scan=None, as_class=None, slave_okay=False, await_data=False,
            partial=False, manipulate=True,
            read_preference=ReadPreference.PRIMARY, tag_sets=[{}],
            secondary_acceptable_latency_ms=None, _must_use_master=False,
            _uuid_subtype=None, **kwargs):
        """Callback used with pymongo collection find call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'spec': spec,
            'fields': fields,
            'skip': skip,
            'limit': limit,
            'timeout': timeout,
            'snapshot': snapshot,
            'tailable': tailable,
            'sort': sort,
            'await_data': await_data,
            'partial': partial,
            'manipulate': manipulate,
            'read_preference': read_preference,
            'tag_sets': tag_sets,
            'secondary_acceptable_latency_ms': secondary_acceptable_latency_ms,
            '_must_use_master': _must_use_master,
            '_uuid_subtype': _uuid_subtype,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_find_and_modify(
            self, custom, collection, query={}, update=None, upsert=False,
            sort=None, full_response=False, **kwargs):
        """Callback used with pymongo collection find_and_modify call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'query': query,
            'update': update,
            'upsert': upsert,
            'sort': sort,
            'full_response': full_response,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_find_one(
            self, custom, collection, spec_or_id=None, fields=None, skip=0,
            limit=0, timeout=True, snapshot=False, tailable=False, sort=None,
            max_scan=None, as_class=None, slave_okay=False, await_data=False,
            partial=False, manipulate=True,
            read_preference=ReadPreference.PRIMARY, tag_sets=[{}],
            secondary_acceptable_latency_ms=None, _must_use_master=False,
            _uuid_subtype=None, **kwargs):
        """Callback used with pymongo collection find_one call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'spec_or_id': spec_or_id,
            'fields': fields,
            'skip': skip,
            'limit': limit,
            'timeout': timeout,
            'snapshot': snapshot,
            'tailable': tailable,
            'sort': sort,
            'await_data': await_data,
            'partial': partial,
            'manipulate': manipulate,
            'read_preference': read_preference,
            'tag_sets': tag_sets,
            'secondary_acceptable_latency_ms': secondary_acceptable_latency_ms,
            '_must_use_master': _must_use_master,
            '_uuid_subtype': _uuid_subtype,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_group(
            self, custom, collection, key, condition, initial, reduce,
            finalize=None):
        """Callback used with pymongo collection group call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'key': key,
            'condition': condition,
            'initial': initial,
            'reduce': reduce,
            'finalize': finalize,
        }
        self.report_command(command)

    def callback_before_collection_inline_map_reduce(
            self, custom, collection, map, reduce, full_response=False,
            **kwargs):
        """Callback used with pymongo collection inline_map_reduce call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'map': map,
            'reduce': reduce,
            'full_response': full_response,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_insert(
            self, custom, collection, doc_or_docs, manipulate=True, safe=None,
            check_keys=True, continue_on_error=False, **kwargs):
        """Callback used with pymongo collection insert call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'doc_or_docs': doc_or_docs,
            'manipulate': manipulate,
            'safe': safe,
            'check_keys': check_keys,
            'continue_on_error': continue_on_error,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_map_reduce(
            self, custom, collection, map, reduce, out, full_response=False,
            **kwargs):
        """Callback used with pymongo collection map_reduce call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'map': map,
            'reduce': reduce,
            'out': out,
            'full_response': full_response,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_remove(
            self, custom, collection, spec_or_id=None, safe=None, **kwargs):
        """Callback used with pumongo collection remove call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'spec_or_id': spec_or_id,
            'safe': safe,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_save(
            self, custom, collection, to_save, manipulate=True, safe=None,
            check_keys=True, **kwargs):
        """Callback used with pumongo collection save call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'to_save': to_save,
            'manipulate': manipulate,
            'safe': safe,
            'check_keys': check_keys,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_collection_update(
            self, custom, collection, spec, document, upsert=False,
            manipulate=False, safe=None, multi=False, check_keys=True,
            **kwargs):
        """Callback used with pymongo collection update call"""
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
            'spec': spec,
            'document': document,
            'upsert': upsert,
            'manipulate': manipulate,
            'safe': safe,
            'multi': multi,
            'check_keys': check_keys,
        }
        command.update(kwargs)
        self.report_command(command)

    def callback_before_cursor_iter(self, custom, cursor):
        """Callback used with pymongo cursor __iter__ call"""
        collection = cursor.collection
        command = {
            'db': collection.database.name,
            'collection': collection.name,
            'op': custom['f'],
        }
        command.update(mongodog.utils.get_pymongo_cursor_fields(cursor))
        self.report_command(command)
