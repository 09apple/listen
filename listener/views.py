from django.http import HttpResponse
from django.shortcuts import render, render_to_response
import logging
import uuid

from listener.replay import get_provider_list
from listener.replay.douban import get_douban_token_ck, get_captcha_token
from listener.models.playlist import PlaylistManager
from listen.settings import MEDIA_ROOT

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
        print('yes login')
        return HttpResponse(dict(isLogin='1'))
    else:
        print('no login')
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
    return HttpResponse(result)


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