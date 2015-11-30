#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PySS's cli - simple script for managing Microsoft Smooth Streaming.

Usage:
    pyss <url> [--debug]
    pyss (-h | --help)
    pyss --version

Options:
    -h --help     Show this screen.
    --version     Show version.
"""
from docopt import docopt
from . import __version__


def main():
    args = docopt(__doc__, version=__version__)
    print(args)


if __name__ == '__main__':
    main()
