"""tournament URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
https://docs.djangoproject.com/en/1.11/topics/http/urls/

Examples:

Function views

    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')

Class-based views

    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')

Including another URLconf

    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import include, path
from django.contrib import admin
from django.http.response import HttpResponseRedirect

urlpatterns = [
    path('', lambda r: HttpResponseRedirect('registration/division/')),
    path(r'registration/', include('registration.urls')),
    path(r'kata/', include('kata.urls')),
    path(r'kumite/', include('kumite.urls')),
    path(r'admin/doc/', include('django.contrib.admindocs.urls')),
    path(r'admin/', admin.site.urls),
    path(r'accounts/', include('accounts.urls')),
    ]
