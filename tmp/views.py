from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin
from django import forms

from .models import *

# Create your views here.
class MyAddressForm():
    class Meta:
        model = MyAddress
        fields = ['address1']

class MyAddressUpdate(UpdateView):
    model = MyAddress
    #form = MyAddressForm
    fields = ['address1', 'phone_number']

class MyAddressCreate(CreateView):
    model = MyAddress
    #form = MyAddressForm
    fields = ['address1', 'phone_number']
