#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
pyss.exceptions
~~~~~~~~~~~~~~~

This module contains the set of fut's exceptions.

"""


class PyssException(RuntimeError):
    """There was an ambiguous exception that occurred while handling
    your request."""


class ConnectionError(PyssException):
    """A Connection error occurred."""
    def __init__(self, code=None, reason=None):
        self.code = code
        self.reason = reason
