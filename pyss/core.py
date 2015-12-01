#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
# import re
import xmltodict
# import subprocess
import time
import sys
from itertools import izip
from .config import headers


class Core(object):
    def __init__(self, user_agent=headers['User-Agent']):
        self.r = requests.Session()
        self.r.headers['User-Agent'] = user_agent

    def __calculateSequence(self, manifest_chunks):
        """Calculates sequence."""
        sequence = []
        for n in range(len(manifest_chunks) - 1):
            lenght = long(manifest_chunks[n + 1]['@t']) - long(manifest_chunks[n]['@t'])
            sequence.append(lenght)
        sequence.append(long(manifest_chunks[-1]['@d']))
        return sequence

    def __manifestChunks__(self, manifest_chunks, interval=1):
        """Helper for parseManifest."""
        # TODO: ability to set time (based on lenght) instead of while True
        # calculate sequence
        sequence = self.__calculateSequence(manifest_chunks)
        for c, l in zip(manifest_chunks, sequence):
            yield (long(c['@t']), l)
        if '@d' in manifest_chunks[-1]:  # it's live stream (or at least we don't know how long it is)
            chunk_last = long(manifest_chunks[-1]['@t'])
            while True:
                for l in range(len(sequence)):
                    time.sleep(interval)
                    chunk_last = chunk_last + sequence[l - 1]
                    yield (chunk_last, sequence[l])

    def parseManifest(self, manifest):
        """Parses manifest."""
        # TODO: move out of Core class
        # TODO: refactor
        # TODO: return object (yield chunks [with content])?
        # TODO: detect sequence (different chunk size [live])
        # TODO: full sequence
        # TODO: add type (audio/video) to stream dict
        manifest = xmltodict.parse(manifest)
        streams = {
            'audio': {'quality': [],
                      'chunks': [],
                      'url': None},
            'video': {'quality': [],
                      'chunks': [],
                      'url': None},
        }
        for i in manifest['SmoothStreamingMedia']['StreamIndex']:
            streams[i['@Type']]['url'] = i['@Url']
            if i['@QualityLevels'] == '1':  # i need a list to operate on
                i['QualityLevel'] = [i['QualityLevel']]
            for q in i['QualityLevel']:
                stream = {
                    'bitrate': q['@Bitrate'],
                    'fourcc': q['@FourCC'],
                    'codecprivatedata': q['@CodecPrivateData']
                }
                if i['@Type'] == 'video':
                    stream['index'] = q['@Index']
                    stream['width'] = q['@MaxWidth']  # DisplayWidth?
                    stream['height'] = q['@MaxHeight']  # DisplayHeight?
                elif i['@Type'] == 'audio':
                    stream['samplingrate'] = q['@SamplingRate']
                    stream['channels'] = q['@Channels']
                    stream['bitspersample'] = q['@BitsPerSample']
                    stream['packetsize'] = q['@PacketSize']
                    stream['audiotag'] = q['@AudioTag']
                streams[i['@Type']]['quality'].append(stream)
            # calculate chunks lenghts
            streams[i['@Type']]['chunks'] = self.__manifestChunks__(i['c'])
        return streams

    def getManifest(self, url):
        """Retrieves manifest, returns parsed (streams)."""
        if not url.lower().endswith('/manifest'):
            if url.endswith('/'):  # is it necessary?
                url = url[:-1]
        rc = self.r.get(url + '/Manifest')
        self.base_url = rc.url[:-9]  # cut '/Manifest'
        return self.parseManifest(rc.content)

    def getChunk(self, stream_url, chunk_time):
        """Returns chunk content."""
        # TODO: throw exception on 404 error (probably wrong sleep time)
        chunk_url = self.base_url + '/' + stream_url.replace('{start time}', str(chunk_time))
        rc = self.r.get(chunk_url)
        if rc.status_code != 200:
            sys.exit(rc.status_code)
        # print rc.status_code  # DEBUG
        return rc.content

    def getStream(self, stream):
        """Yields all chunks from given stream."""
        # TODO: add drm support (rightsmanager.asmx) ?
        # TODO: ability to manipulate loop lenght (for example finish after 30min)
        # TODO: detect best quality
        # TODO: detect live
        # todo: ability to choose quality
        stream_url = stream['url'].replace('{bitrate}', stream['quality'][0]['bitrate'])
        for chunk in stream['chunks']:
            # return chunk[0]
            yield self.getChunk(stream_url, chunk[0])
            # return self.getChunk(stream_url, chunk[0])

    def getStreams(self, streams):
        """Retrieves streams (first audio and first video)"""
        # TODO: write offline manifest
        # TODO: ability to manipulate loop lenght (for example finish after 30min)
        # TODO: detect best quality
        # TODO: detect live
        # todo: ability to choose quality
        for i in izip(self.getStream(streams['video']), self.getStream(streams['audio'])):
            yield i
