from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.test_bracket),
    # url(r'^person/add/$', views.PersonCreate.as_view(), name='create'),
    # url(r'^person/(?P<pk>[0-9]+)/$', views.DetailView.as_view(), name='detail'),
    # url(r'^person/(?P<pk>[0-9]+)/edit/$', views.PersonUpdate.as_view(), name='update'),
    # url(r'^person/(?P<pk>[0-9]+)/delete/$', views.PersonDelete.as_view(), name='delete'),
    # url(r'^division/$', views.DivisionList.as_view(), name='divisions')
    # url(r'new/', views.NewView.as_view())
]