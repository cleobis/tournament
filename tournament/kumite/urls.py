from django.conf.urls import url

from . import views

app_name = 'kumite'
urlpatterns = [
    url(r'^bracket-n/(?P<pk>[0-9]+)/$', views.BracketDetails.as_view(), name='bracket-n'),
    url(r'^bracket-n(?P<pk>[0-9]+)/delete/$', views.BracketDelete.as_view(), name='bracket-n-delete'),
    
    url(r'^bracket-rr/(?P<pk>[0-9]+)/$', views.BracketRoundRobinDetails.as_view(), name='bracket-rr'),
    url(r'^bracket-rr/(?P<pk>[0-9]+)/delete/$', views.BracketRoundRobinDelete.as_view(), name='bracket-rr-delete'),
    
    url(r'^bracket-2/(?P<pk>[0-9]+)/$', views.Bracket2PeopleDetails.as_view(), name='bracket-2'),
    url(r'^bracket-2/(?P<pk>[0-9]+)/delete/$', views.Bracket2PeopleDelete.as_view(), name='bracket-2-delete'),
    
    url(r'^match/manual/edit/', views.KumiteMatchManual.as_view(), name='manual-match'),
    url(r'^match/(?P<pk>[0-9]+)/edit/', views.KumiteMatchUpdate.as_view(), name='match'),
]