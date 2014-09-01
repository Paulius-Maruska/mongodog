# -*- coding: utf-8 -*-
"""
MongoDog is a library designed to sniff out the things that your application
is doing within a mongo database. It plugs itself in between your app and
pymongo and logs all of the commands
that your application sends to the server.
"""

__author__ = "Paulius Maruška"
__version__ = "0.1.0"

from mongodog.reporters import BaseReporter, MemoryReporter, LoggingReporter
from mongodog.sniffer import Sniffer

__all__ = [
    "__author__",
    "__version__",
    "BaseReporter",
    "MemoryReporter",
    "LoggingReporter",
    "Sniffer",
]
