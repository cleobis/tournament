from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^address/new/$', views.MyAddressCreate.as_view()),
    url(r'^address/(?P<pk>[0-9]+)/$', views.MyAddressUpdate.as_view(), name='edit-address'),
]