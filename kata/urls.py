from django.conf.urls import url

from . import views

app_name = 'kata'

urlpatterns = [
#    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^(?P<pk>[0-9]+)/$', views.KataBracketDetails.as_view(), name='bracket'),
    url(r'^(?P<bracket>[0-9]+)/edit/(?P<pk>[0-9]+)/$', views.KataBracketEditMatch.as_view(), name='bracket-match-edit'),
    url(r'^(?P<bracket>[0-9]+)/delete/(?P<pk>[0-9]+)/$', views.KataBracketDeleteMatch.as_view(), name='bracket-match-delete'),
    url(r'^(?P<pk>[0-9]+)/add/$', views.KataBracketAddMatch.as_view(), name='bracket-match-add'),
#    url(r'^person/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
#    url(r'^person/(?P<pk>[0-9]+)/edit/$', views.PersonUpdate.as_view(), name='update'),
#    url(r'^person/(?P<pk>[0-9]+)/delete/$', views.PersonDelete.as_view(), name='delete'),
#    url(r'^division/$', views.DivisionList.as_view(), name='divisions')
    #url(r'new/', views.NewView.as_view())
]