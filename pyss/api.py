#!/usr/bin/env python
# -*- coding: utf-8 -*-
from . import Core
from .config import headers


def download(url, dest='.', user_agent=headers['User-Agent'], duration=float('inf')):
    """Download stream."""
    # TODO: ability to set quality
    video_parts = []
    audio_parts = []
    c = Core(user_agent)
    streams = c.getManifest(url)
    if c.live:
        print('Downloading live stream...')
    else:
        print('Downloading [n] chunks...')
    try:
        for v, a in c.getStreams(streams, duration=duration):
            with open(v['path'], 'wb') as fv:
                fv.write(v['content'])
                video_parts.append(v['path'])
            with open(a['path'], 'wb') as fa:
                fa.write(a['content'])
                audio_parts.append(a['path'])
    except KeyboardInterrupt:
        pass
    # c.createManifest(audio_parts, video_parts)  # not done yet


# todo: play?
