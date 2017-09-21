from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.IndexView.as_view(), name='index'),
    url(r'^person/add/$', views.PersonCreate.as_view(), name='create'),
    url(r'^person/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    url(r'^person/(?P<pk>[0-9]+)/edit/$', views.PersonUpdate.as_view(), name='update'),
    url(r'^person/(?P<pk>[0-9]+)/delete/$', views.PersonDelete.as_view(), name='delete'),
    url(r'^division/$', views.DivisionList.as_view(), name='divisions'),
    url(r'^division/(?P<pk>[0-9]+)/$', views.DivisionInfoDispatch.as_view(), name='division-detail'),
    url(r'^division/(?P<pk_div>[0-9]+)/delete/(?P<pk>[0-9]+)/$', views.DivisionDeleteManaualPerson.as_view()),
]