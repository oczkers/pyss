#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import Core
from .config import headers


def download(url, user_agent=headers['User-Agent']):
    """Downloads stream."""
    # TODO: ability to set quality, time
    c = Core(user_agent)
    streams = c.getManifest(url)
    c.getStreams(streams)  # work in progress


# todo: play?
