#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PySS's cli - simple script for managing Microsoft Smooth Streaming.

Usage:
    pyss (download | dl) <url> [--user-agent=<user-agent>] [--verbose] [--debug]
    pyss (-h | --help)
    pyss --version

Options:
    -h --help     Show this screen.
    --version     Show version.
    --verbose     Be more verbose
    --debug       Debug (saves logs)
    -ua <user-agent>, --user-agent=user-<agent>  User-Agent string.
"""
from docopt import docopt
from . import __version__, download
from .config import headers


def main():
    # TODO: default user-agent string in docopt.
    args = docopt(__doc__, version=__version__)
    if args['--user-agent'] == 'null':
        args['--user-agent'] = headers['User-Agent']
    print(args)
    if args['download'] or args['dl']:
        download(args['<url>'], user_agent=args['--user-agent'], debug=args['--debug'])


if __name__ == '__main__':
    main()
