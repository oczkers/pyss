#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
# import re
import xmltodict
# import subprocess
import time
import sys
if sys.version_info[0] == 2:
    from itertools import izip as zip
try:
    from lxml import etree
except ImportError:
    from xml.etree import cElementTree as etree
from .config import headers
from .exceptions import ConnectionError


class Manifest(dict):
    def __init__(self):
        self.timescale = 10000000
        pass

    @property
    def xml(self):
        # http://lxml.de/tutorial.html
        x = etree.Element(  # TODO: calculate duration
            'SmoothStreamingMedia', MajorVersion='2', MinorVersion='1',
            Duration='0', Timescale=str(self.timescale),
            LookAheadFragmentCount='2', DVRWindowLenght='0', IsLive='False'
        )
        return etree.tostring(x, xml_declaration=True, encoding='utf-8')

    def addStream(self, stream):
        pass


class Core(object):
    def __init__(self, user_agent=headers['User-Agent']):
        self.r = requests.Session()
        self.r.headers['User-Agent'] = user_agent
        self.live = False  # it shouldn't be this way

    def __calculateSequence(self, manifest_chunks):
        """Calculates sequence."""
        sequence = []
        for n in range(len(manifest_chunks) - 1):
            lenght = long(manifest_chunks[n + 1]['@t']) - long(manifest_chunks[n]['@t'])
            sequence.append(lenght)
        sequence.append(long(manifest_chunks[-1]['@d']))
        return sequence

    def __manifestChunks__(self, manifest_chunks, interval=2):
        """Helper for parseManifest."""
        # TODO: adjust interval based on chunk time/sequence instead of real time
        # calculate sequence
        sequence = self.__calculateSequence(manifest_chunks)
        for c, l in zip(manifest_chunks, sequence):
            yield (long(c['@t']), l)
        if '@d' in manifest_chunks[-1]:  # it's live stream (or at least we don't know how long it is)
            self.live = True
            chunk_last = long(manifest_chunks[-1]['@t'])
            chunk_time = time.time()
            while True:
                for l in range(len(sequence)):
                    chunk_time += interval
                    chunk_interval = chunk_time - time.time()
                    if chunk_interval < 0:
                        print('WARNING: i am to slow (interval is bigger than %s)' % interval)
                    time.sleep(max(0, chunk_interval))
                    chunk_last = chunk_last + sequence[l - 1]
                    yield (chunk_last, sequence[l])

    def parseManifest(self, manifest):
        """Parses manifest."""
        # TODO: move out of Core class?
        # TODO: refactor
        # TODO: return object (yield chunks [with content])?
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
        chunk_path = stream_url.replace('{start time}', str(chunk_time))
        chunk_url = self.base_url + '/' + chunk_path
        rc = self.r.get(chunk_url)
        if rc.status_code != 200:
            raise ConnectionError(rc.status_code, rc.reason)
        # print(rc.status_code)  # DEBUG
        return {'id': chunk_time, 'path': chunk_path, 'content': rc.content}

    def getStream(self, stream, duration=float('inf')):
        """Yields all chunks from given stream."""
        # TODO: add drm support (rightsmanager.asmx) ?
        # TODO: detect best quality
        # todo: ability to choose quality
        time_end = time.time() + duration
        stream_url = stream['url'].replace('{bitrate}', stream['quality'][0]['bitrate'])
        for chunk in stream['chunks']:
            if time.time() > time_end:
                break
            # return chunk[0]
            yield self.getChunk(stream_url, chunk[0])
            # return self.getChunk(stream_url, chunk[0])

    def getStreams(self, streams, duration=float('inf')):
        """Retrieves streams (first audio and first video)"""
        # TODO: multithread
        # TODO: write offline manifest
        # TODO: detect best quality
        # todo: ability to choose quality
        for i in zip(self.getStream(streams['video'], duration=duration), self.getStream(streams['audio'], duration=duration)):
            yield i
