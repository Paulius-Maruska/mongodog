# -*- coding: utf-8 -*-
"""
Setup configuration
"""
__author__ = "Paulius Maruška"
__version__ = "0.1.0"

try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages

try:
    with open("README.md") as f:
        README = f.read()
except:
    README = ""

try:
    with open("LICENSE") as f:
        LICENSE = f.read()
except:
    LICENSE = ""

DESCRIPTION="""
MongoDog is a library designed to sniff out the things that your application is doing within
a mongo database. It plugs itself in between your app and pymongo and logs all of the commands
that your application sends to the server.
"""

setup(
    name='mongodog',
    version=__version__,
    description=DESCRIPTION,
    long_description=README,
    url='https://github.com/Paulius-Maruska/mongodog',
    license=LICENSE,
    author=__author__,
    author_email='paulius.maruska@gmail.com',
    packages=find_packages(exclude=('tests',)),
    include_package_data=True,
    install_requires=[],
    zip_safe=False,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Plugins',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: Apache Software License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development'
    ],
    tests_require=["nose", "pymongo", "mongobox"],
    test_suite = "nose.collector",
)
