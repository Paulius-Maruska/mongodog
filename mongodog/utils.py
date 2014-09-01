# -*- coding: utf-8 -*-
"""Helper functions"""
import sys


def get_full_traceback(skip=0):
    """Get full traceback.
    inspired by: http://stackoverflow.com/questions/13210436/#13210518

    :Parameters:
    - `skip`: top frames to be skipped.

    :Returns:
    An object compatible with the pythons built-in traceback object. It isn't
    the same kind of object, but most traceback formatting functions should
    accept it.

    :Note:
    This function raises a dummy exception in order to make sure the traceback
    is populated by python. Do not call this function within your own exception
    handlers, because you will lose your actual traceback information.
    """
    class FakeTracebackFrame(object):
        """Fake traceback frame class"""
        def __init__(self, tb_frame, tb_lineno, tb_next):
            self.tb_frame = tb_frame
            self.tb_lineno = tb_lineno
            self.tb_next = tb_next

    class DummyException(Exception):
        """Dummy exception we raise, to get the traceback"""
        pass

    try:
        raise DummyException()
    except DummyException:
        _, _, exc_traceback = sys.exc_info()

    f = exc_traceback.tb_frame

    for _ in range(skip + 1):
        f = f.f_back

    head = None
    while f is not None:
        tb_frame, tb_lineno = f, f.f_lineno
        head = FakeTracebackFrame(tb_frame, tb_lineno, head)
        f = f.f_back

    return head


def get_pymongo_cursor_fields(cursor):
    """Get a dictionary with all (or most) significant field values of the
    pymongo Cursor object"""
    fields = ("spec", "fields", "skip", "limit",
              "timeout", "snapshot", "tailable",
              "ordering", "explain", "hint", "batch_size",
              "max_scan", "as_class", "slave_okay", "await_data",
              "partial", "manipulate", "read_preference",
              "tag_sets", "secondary_acceptable_latency_ms",
              "must_use_master", "uuid_subtype", "query_flags",
              "kwargs")
    return {field: cursor.__dict__.get('_Cursor__%s' % field, None)
            for field in fields}
