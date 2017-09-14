from django.http import HttpResponse
from django.shortcuts import render, render_to_response, redirect
import logging
import uuid
import errno
import time
import shutil

from django.test import Client

from listener.replay import get_provider_list, get_provider_by_name
from listener.replay.douban import get_douban_token_ck, get_captcha_token
from listener.models.playlist import PlaylistManager
from listen.settings import MEDIA_ROOT
import json
import os

logger = logging.getLogger('listenone.' + __name__)

def index(request):
    return render(request, 'listener/index.html'
                    )

'''
 handlers
'''

def ValidCode(request):
    token, ck = get_douban_token_ck()
    if token is not None and ck is not None:
        return HttpResponse(dict(isLogin='1'))
    else:
        return HttpResponse(dict(isLogin='0', captcha=_get_captcha()))

# search
def Search(request):
    source = request.GET.get('source', '0')
    keywords = request.GET.get('keywords', '0')
    result = dict(result=[])
    if keywords == '':
        return HttpResponse(result)

    provider_list = get_provider_list()

    index = int(source)
    if index >= 0 and index < len(provider_list):
        provider = provider_list[index]
        track_list = provider.search_track(keywords)
    else:
        track_list = []

    result = dict(result=track_list)
    return HttpResponse(json.dumps(result))


# playlist
def ShowPlayList(request):
    source = request.GET.get('source', '0')

    provider_list = get_provider_list()
    index = int(source)
    if index >= 0 and index < len(provider_list):
        provider = provider_list[index]
        playlist = provider.list_playlist()
    else:
        playlist = []

    result = dict(result=playlist)
    return HttpResponse(result)

def trackFile(request):
    url = request.GET.get('url', '')
    artist = request.GET.get('artist')
    album = request.GET.get('album')
    title = request.GET.get('title')
    sid = request.GET.get('id')
    source = request.GET.get('source', '')
    download = request.GET.get('download', '')

    provider = get_provider_by_name(source)

    # local cache hit test
    ext = 'mp3'
    if url != '':
        ext = url.split('.')[-1]
    else:
        ext = provider.filetype()[1:]

    file_path = os.path.join(
        MEDIA_ROOT, 'music', artist, album, title +
                                            '_' + sid + '.' + ext)

    if os.path.isfile(file_path) and download != '1':
        redirect_url = os.path.join(
            '/static/music/', artist, album,
            title + '_' + sid + '.' + ext)
        redirect(redirect_url, False)
        return

    if url == '':
        sid = sid.split('_')[1]
        url = provider.get_url_by_id(sid)

    user_agent = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_1) ' + \
                 'AppleWebKit/537.36 (KHTML, like Gecko) ' + \
                 'Chrome/46.0.2490.86 Safari/537.36'
    referer = 'http://douban.fm/'
    xwith = 'ShockwaveFlash/19.0.0.245'
    headers = {
        'User-Agent': user_agent,
        'Referer': referer,
        'X-Requested-With': xwith,
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6,ja;q=0.4,zh-TW;q=0.2',
        'Accept-Encoding': 'gzip, deflate, sdch',
    }

    # read range from request header
    req_range = request.headers.get('Range', '')

    if req_range != '':
        headers['Range'] = req_range

    request = Client.httpclient.HTTPRequest(
        url=url, headers=headers,
        streaming_callback=Client._on_chunk,
        header_callback=Client._on_header)

    Client.fetch(request, Client._on_download)

    # self.set_status(206)

    Client.bytes_so_far = 0

    if download == '1':
        Client.set_header('Content-Type', 'application/force-download')
        filename = title + '_' + artist + '.' + ext
        Client.set_header(
            'Content-Disposition',
            'attachment; filename="%s"' % filename)

    if not os.path.exists(os.path.dirname(file_path)):
        try:
            os.makedirs(os.path.dirname(file_path))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    timestamp_string = str(time.time()).replace('.', '')
    Client.tmp_file_path = file_path + '.' + timestamp_string
    Client.fd = open(Client.tmp_file_path, 'wb')


def _chunk(self, data):
    self.write(data)
    self.flush()

def _parse_header_string(self, header_string):
    comma_index = header_string.find(':')
    k = header_string[:comma_index]
    v = header_string[comma_index + 1:].strip()
    return k, v

def _on_header(self, header):
    k, v = self._parse_header_string(header)
    if k in [
        'Content-Length', 'Accept-Ranges',
        'Content-Type', 'Content-Range',
        'Accept-Ranges', 'Connection']:
        self.set_header(k, v)
    if header.startswith('Content-Length'):
        self.total_size = int(header[len('Content-Length:'):].strip())

def _on_chunk(self, chunk):
    self.write(chunk)
    self.flush()
    self.fd.write(chunk)
    self.bytes_so_far += len(chunk)

def _on_download(self, response):
    self.finish()
    self.fd.close()
    # check if file size equals to content_length
    size = 0
    with open(self.tmp_file_path, 'r') as check_fd:
        check_fd.seek(0, 2)
        size = check_fd.tell()

    if size > 2 and size == self.total_size:
        '''
        why size will less than 2:
        safari browser will prerequest url with byte range 2,
        so maybe generate temp file with 2 bytes.
        '''
        timestamp_string = self.tmp_file_path.split('.')[-1]
        target_path = self.tmp_file_path[:-(len(timestamp_string) + 1)]
        shutil.move(self.tmp_file_path, target_path)
    else:
        os.remove(self.tmp_file_path)


def ShowMyPlayList(request):
    resultlist = PlaylistManager.shared_instance(). \
        list_playlist()
    result = dict(result=resultlist)
    print(result)
    return HttpResponse(result)


'''
  methods
'''


def _get_captcha():
    # get valid code from douban server
    # save it to temp folder
    filename = str(uuid.uuid4()) + '.jpg'
    path = MEDIA_ROOT + '/temp/' + filename
    token = get_captcha_token(path)
    print(dict(path='/static/temp/' + filename, token=token))
    return dict(path='/static/temp/' + filename, token=token)