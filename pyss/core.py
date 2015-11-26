#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
# import re
import xmltodict
# import subprocess
import time
import sys
from .config import headers

base_url = 'http://host.tld/channel.smil'  # get this from manifest url


class Core(object):
    # TODO: add getManifest
    # TODO: getManifest in init
    # TODO: detect url change in getManifest (balancer sends us to different host)
    # TODO: add specific user-agents and settings (for netia tv for example)
    def __init__(self):
        self.r = requests.Session()
        self.r.headers = headers

    def parseManifest(self, manifest):
        """Parses manifest."""
        # TODO: detect sequence (different chunk size [live])
        # TODO: full sequence
        manifest = xmltodict.parse(manifest)
        streams = {
            'audio': {'quality': [],
                      'chunks': [],
                      'url': None,
                      'chunkd': 0},
            'video': {'quality': [],
                      'chunks': [],
                      'url': None,
                      'chunkd': 0},
        }
        for i in manifest['SmoothStreamingMedia']['StreamIndex']:
            streams[i['@Type']]['url'] = i['@Url']
            if i['@QualityLevels'] == '1':
                i['QualityLevel'] = [i['QualityLevel']]
            for q in i['QualityLevel']:
                stream = {
                    'bitrate': q['@Bitrate'],
                    'fourcc': q['@FourCC'],
                    'codecprivatedata': q['@CodecPrivateData']
                }
                if '@MaxWidth' in q:  # video
                    stream['index'] = q['@Index']
                    stream['width'] = q['@MaxWidth']  # DisplayWidth?
                    stream['height'] = q['@MaxHeight']  # DisplayHeight?
                elif '@SamplingRate' in q:  # audio
                    stream['samplingrate'] = q['@SamplingRate']
                    stream['channels'] = q['@Channels']
                    stream['bitspersample'] = q['@BitsPerSample']
                    stream['packetsize'] = q['@PacketSize']
                    stream['audiotag'] = q['@AudioTag']
                streams[i['@Type']]['quality'].append(stream)
            for c in i['c']:
                streams[i['@Type']]['chunks'].append(c['@t'])
            streams[i['@Type']]['chunkd'] = i['c'][-1]['@d']
        return streams

    def getChunks(self, chunks, filename):
        """Downloads all chunks."""
        # TODO: return chunk instead of saving as a file.
        for c in chunks:
            f = filename.replace('{start time}', c)
            url = base_url + '/' + f
            with open(f, 'wb') as f:
                f.write(self.r.get(url).content)

    def getStreams(self, streams):
        """Retrieves streams (first audio and first video)."""
        # TODO: detect best quality
        # todo: ability to choose quality
        for stream in streams.values():
            filename = stream['url'].replace('{bitrate}', stream['quality'][0]['bitrate'])
            self.getChunks(stream['chunks'], filename)

    def live(self, streams):
        """Retrieves live chunks in while loop."""
        # TODO: move chunk sequence detection to parseManifest
        # TODO: throw exception on 404 error (probably wrong sleep time)
        # TODO: be a generator instead of saving files
        # TODO: ability to manipulate loop lenght (for example finish after 30min)
        # TODO: async to avoid 404
        # TODO: write offline manifest
        # TODO: add drm support (rightsmanager.asmx) ?
        chunk_video = streams['video']['chunks'][-1]
        chunk_audio = streams['audio']['chunks'][-1]
        chunk_sequence = (
            (int(streams['video']['chunkd']), int(streams['audio']['chunkd'])),
            (int(streams['video']['chunkd']), int(streams['audio']['chunks'][1]) - int(streams['audio']['chunks'][0])),
            (int(streams['video']['chunkd']), int(streams['audio']['chunks'][2]) - int(streams['audio']['chunks'][1]))
        )
        while True:
            for chunkd_video, chunkd_audio in chunk_sequence:
                chunk_video = str(int(chunk_video) + chunkd_video)
                chunk_audio = str(int(chunk_audio) + chunkd_audio)
                # chunk_audio = str(int(chunk_audio) + 10000)
                # video
                filename = streams['video']['url'].replace('{bitrate}', streams['video']['quality'][0]['bitrate']).replace('{start time}', chunk_video)
                print filename
                url = base_url + '/' + filename
                with open(filename, 'wb') as f:
                    rc = self.r.get(url)
                    if rc.status_code != 200: sys.exit(rc.status_code)
                    f.write(rc.content)
                # audio
                # ... 6 5 5 6 5 5 6 5 5 ...
                filename = streams['audio']['url'].replace('{bitrate}', streams['audio']['quality'][0]['bitrate']).replace('{start time}', chunk_audio)
                print filename
                url = base_url + '/' + filename
                with open(filename, 'wb') as f:
                    rc = self.r.get(url)
                    if rc.status_code != 200: sys.exit(rc.status_code)
                    f.write(rc.content)
                time.sleep(1)
