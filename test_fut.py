#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for pyss."""

import unittest

import pyss


class pyssTestCase(unittest.TestCase):

    # _multiprocess_can_split_ = True

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def testEntryPoints(self):
        pyss.Core


if __name__ == '__main__':
    unittest.main()
