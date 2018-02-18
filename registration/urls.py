from django.conf.urls import url

from . import views

app_name = 'registration'
urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^table/$', views.IndexViewTable.as_view(), name='index-table'),
    url(r'^table/(?P<pk>[0-9]+)/$', views.IndexViewTableRow.as_view(), name='index-table-row'),
    url(r'^person/add/$', views.PersonCreate.as_view(), name='create'),
    url(r'^person/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^person/(?P<pk>[0-9]+)/edit/$', views.PersonUpdate.as_view(), name='update'),
    url(r'^person/(?P<pk>[0-9]+)/delete/$', views.PersonDelete.as_view(), name='delete'),
    url(r'^person/(?P<pk>[0-9]+)/checkin/$', views.PersonCheckin.as_view(), name='person-checkin'),
    url(r'^person/(?P<pk>[0-9]+)/paid/$', views.PersonPaid.as_view(), name='person-paid'),
    url(r'^division/$', views.DivisionList.as_view(), name='divisions'),
    url(r'^division/(?P<pk>[0-9]+)/$', views.DivisionInfoDispatch.as_view(), name='division-detail'),
    url(r'^division/(?P<pk_div>[0-9]+)/delete/(?P<pk>[0-9]+)/$', views.DivisionDeleteManaualPerson.as_view()),
    url(r'^division/(?P<pk>[0-9]+)/build/$', views.DivisionBuild.as_view()),
]