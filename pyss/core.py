#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
# import re
import xmltodict
# import subprocess
import time
import sys
from .config import headers


class Core(object):
    def __init__(self, user_agent=headers['User-Agent']):
        self.r = requests.Session()
        self.r.headers['User-Agent'] = user_agent

    def parseManifest(self, manifest):
        """Parses manifest."""
        # TODO: move out of Core class
        # TODO: refactor
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
            for n in range(len(i['c']) - 1):
                chunk_lenght = int(i['c'][n + 1]['@t']) - int(i['c'][n]['@t'])
                streams[i['@Type']]['chunks'].append((int(i['c'][n]['@t']), chunk_lenght))
            # TODO: calulcate last chunk time (and add next one if @d is present)
            # calculate last chunk lenght
            if '@d' in i['c'][-1]:
                chunk_last = int(i['c'][-1]['@t']) + int(i['c'][-1]['@d'])
                chunk_lenght = chunk_last - int(i['c'][-1]['@t'])
                streams[i['@Type']]['chunks'].append((int(i['c'][-1]['@t']), chunk_lenght))
            else:
                chunk_last = int(i['c'][-1]['@t'])
            chunk_lenght = streams[i['@Type']]['chunks'][-1][1]  # blind guess it's the same as before  # TODO: calculate this
            streams[i['@Type']]['chunks'].append((chunk_last, chunk_lenght))
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
        chunk_url = stream_url.replace('{start time}', chunk_time)
        return self.r.get(chunk_url).content

    def getStream(self, stream):
        """Yields all chunks from given stream."""
        # TODO: detect best quality
        # TODO: detect live
        # todo: ability to choose quality
        stream_url = stream['url'].replace('{bitrate}', stream['quality'][0]['bitrate'])
        for chunk_time in stream['chunks']:
            yield self.getChunk(stream_url, chunk_time)

    def getStreams(self, streams):
        """Retrieves streams (first audio and first video)"""
        # TODO: detect best quality
        # TODO: detect live
        # todo: ability to choose quality
        pass

    def getStreamsLive(self, streams, interval=1):
        """Retrieves live chunks in while loop."""
        # TODO: move chunk sequence detection to parseManifest
        # TODO: throw exception on 404 error (probably wrong sleep time)
        # TODO: be a generator instead of saving files, return (video, audio)
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
                url = self.base_url + '/' + filename
                with open(filename, 'wb') as f:
                    rc = self.r.get(url)
                    if rc.status_code != 200: sys.exit(rc.status_code)
                    f.write(rc.content)
                # audio
                # ... 6 5 5 6 5 5 6 5 5 ...
                filename = streams['audio']['url'].replace('{bitrate}', streams['audio']['quality'][0]['bitrate']).replace('{start time}', chunk_audio)
                print filename
                url = self.base_url + '/' + filename
                with open(filename, 'wb') as f:
                    rc = self.r.get(url)
                    if rc.status_code != 200: sys.exit(rc.status_code)
                    f.write(rc.content)
                time.sleep(interval)
