from django.conf.urls import url

from listener import views

urlpatterns = [

    url(r'^$', views.index, name='index'),

    url(r'^track_file', views.trackFile, name='trackfile'),

    url(r'^search', views.Search, name='search'),
    url(r'^dbvalidcode', views.ValidCode, name='validcode'),
    url(r'^show_playlist', views.ShowPlayList, name='showplaylist'),
    url(r'^show_myplaylist', views.ShowMyPlayList, name='showmyplaylist'),


    # url(r'^images/(?P<path>.*)$', 'static.server', {'document_root': sett})

]