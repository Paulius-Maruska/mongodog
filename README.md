mongodog
========

A python library, that helps you sniff out your own code that is running on mongo (using pymongo or mongokit).

Why?
====

Mongo has profile functionality and it is great. Why do we need mongodog? Well, mongodog includes one very important
feature that mongo profile doesn't - python traceback of the calling code. Sometimes you just need to know where the
command is coming from.
