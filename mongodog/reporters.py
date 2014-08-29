# -*- coding: utf-8 -*-
"""
Defines mongodog reporters.
"""
import json
import logging


class BaseReporter(object):
    """Abstract reporter interface"""

    def report_mongo_command(self, command, traceback=None):
        """Abstract method, called on all sniffed out commands that pymongo performs on the mongodb."""
        raise NotImplementedError("report_mongo_command was not implemented in %s" % self.__class__.__name__)


class MemoryReporter(BaseReporter):
    """Does not report anything to anywhere, simply collects all commands in a list"""

    def __init__(self):
        self.reported_commands = []

    def report_mongo_command(self, command, traceback=None):
        """Adds command to `self.reported_commands`"""
        self.reported_commands.append((command, traceback))


class LoggingReporter(BaseReporter):
    """Reports the calls to configured logger"""

    def __init__(self, logger_or_name):

        try:
            bs = basestring
        except NameError:
            # must be python3
            bs = str, bytes

        if isinstance(logger_or_name, logging.Logger):
            self.logger = logger_or_name
        elif isinstance(logger_or_name, bs):
            self.logger = logging.getLogger(logger_or_name)
        else:
            raise ValueError("LoggingReporter expects either a logging.Logger object or a str object (logger name)")

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
