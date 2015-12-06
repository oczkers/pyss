#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import Core
from .config import headers


def download(url, dest='.', user_agent=headers['User-Agent']):
    """Downloads stream."""
    # TODO: ability to set quality, time
    c = Core(user_agent)
    streams = c.getManifest(url)
    if c.live:
        print 'Downloading live stream...'
    else:
        print 'Downloading [n] chunks...'
    n = 1
    for v, a in c.getStreams(streams):
        with open('%s/video/%s' % (dest, n), 'wb') as fv:
            fv.write(v)
        with open('%s/audio/%s' % (dest, n), 'wb') as fa:
            fa.write(a)
        n += 1


# todo: play?
