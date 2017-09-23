from django.conf.urls import url

from . import views

app_name = 'kumite'
urlpatterns = [
    url(r'^(?P<pk>[0-9]+)/$', views.BracketDetails.as_view(), name='bracket'),
    url(r'^(?P<pk>[0-9]+)/delete/$', views.BracketDelete.as_view(), name='bracket-delete'),
    url(r'^match/manual/edit/', views.KumiteMatchManual.as_view(), name='manual-match'),
    url(r'^match/(?P<pk>[0-9]+)/edit/', views.KumiteMatchUpdate.as_view(), name='match'),
    # url(r'^person/add/$', views.PersonCreate.as_view(), name='create'),
    # url(r'^person/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # url(r'^person/(?P<pk>[0-9]+)/edit/$', views.PersonUpdate.as_view(), name='update'),
    # url(r'^person/(?P<pk>[0-9]+)/delete/$', views.PersonDelete.as_view(), name='delete'),
    # url(r'^division/$', views.DivisionList.as_view(), name='divisions')
    # url(r'new/', views.NewView.as_view())
]