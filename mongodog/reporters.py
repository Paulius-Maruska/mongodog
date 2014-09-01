# -*- coding: utf-8 -*-
"""
Defines mongodog reporters.
"""
import json
import logging
import traceback as python_traceback


class BaseReporter(object):
    """Abstract reporter interface"""

    def report_mongo_command(self, _command, _traceback=None):
        """Abstract method, called on all sniffed out commands that pymongo
        performs on the mongodb."""
        cls = self.__class__.__name__
        message = "report_mongo_command was not implemented in %s" % cls
        raise NotImplementedError(message)


class MemoryReporter(BaseReporter):
    """Does not report anything to anywhere, simply collects all commands
    in a list"""

    def __init__(self):
        self.reported_commands = []

    def report_mongo_command(self, command, traceback=None):
        """Adds command to `self.reported_commands`"""
        self.reported_commands.append((command, traceback))


class LoggingReporter(BaseReporter):
    """Reports the calls to configured logger"""

    def __init__(self, logger_or_name):

        try:
            string_type = basestring
        except NameError:
            # must be python3
            string_type = str, bytes

        if isinstance(logger_or_name, logging.Logger):
            self.logger = logger_or_name
        elif isinstance(logger_or_name, string_type):
            self.logger = logging.getLogger(logger_or_name)
        else:
            raise ValueError("LoggingReporter expects either a logging.Logger"
                             " object or a str object (logger name)")

        # loggers can not include traceback without exception info
        # so we use this exception class for the job
        self.exc_class = Exception

    def report_mongo_command(self, command, traceback=None):
        """Logs the command to configured logger"""
        exc_info = None
        if traceback is not None:
            exc_info = self.exc_class, self.exc_class(), traceback
        command_json = json.dumps(command)
        log_message = "mongodog: %s" % command_json
        self.logger.info(log_message, exc_info=exc_info)


class MongoReporter(BaseReporter):
    """Reports the calls into the configured mongo collection (does not
    report it's own calls)"""

    def __init__(self, mongo_collection):

        self.collection = mongo_collection

    def report_mongo_command(self, command, traceback=None):
        """Logs the command to configured mongo collection"""
        # ignore all commands, that involve the collection we
        # are configured to use
        if command.get('collection', None) == self.collection.name:
            return

        types = bool, int, float
        try:
            types = types + (long, basestring)
        except NameError:
            # must be python3
            types = types + (str, bytes)

        document = {}
        for key, val in command.items():
            if isinstance(val, types):
                document[key] = val
            else:
                try:
                    document[key] = json.dumps(val)
                except TypeError:
                    # json raises TypeError, when trying to serialize
                    # something has no support for
                    document[key] = repr(val)
                    # ir repr fails - we give up and let the app crash

        document['_traceback'] = python_traceback.format_tb(traceback)

        self.collection.insert(document)
