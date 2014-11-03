__author__ = 'stefano'

import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

# https://pypi.python.org/pypi?%3Aaction=list_classifiers
setup(
    name = "GymCentral - API App",
    version = "0.0.1",
    author = "Stefano Tranquillini",
    author_email = "stefano.tranquillini@gmail.com",
    description = ("The API App used in GC"),
    license = "MIT",
    packages=['gymcentral',],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Software Development",
        "License :: OSI Approved :: MIT License",
    ],
)