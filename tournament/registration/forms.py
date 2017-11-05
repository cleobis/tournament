from django import forms
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db.models import F, Q, Value
from django.db.models.functions import Concat

from .models import Person, Rank, EventLink


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'gender', 'age', 'rank', 'instructor', 'phone_number', 'email', 'paid', 'events', 'notes']
        widgets = {
            'events': forms.CheckboxSelectMultiple(),
        }


class ManualEventLinkForm(forms.ModelForm):
    class Meta:
        model = EventLink
        fields = ['manual_name', ]
        labels = {'manual_name': 'Name'}
    
    def __init__(self, division=None, **kwargs):
        self.division = division
        super().__init__(**kwargs)
        self.fields['manual_name'].widget.attrs.update({'autofocus': 'autofocus'})
    
    
    def clean_manual_name(self):
        data = self.cleaned_data['manual_name']
        if len(data) == 0:
            raise ValidationError('Name cannot be empty.')
        return data
    
    
    def clean(self):
        
        super().clean()
        
        if self.division is None:
            raise ValidationError('Division not assigned.')
        
        self.instance.event = self.division.event
        self.instance.division = self.division


class PersonFilterForm(forms.Form):
    name = forms.CharField(required=False)
    paid = forms.TypedChoiceField(required=False, choices=((None, 'Any'), (True, 'Yes'), (False, 'No'),), 
        coerce=lambda x: True if x == 'True' else False if x == 'False' else None, empty_value=None)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        common_attrs = {'ic-get-from':reverse('registration:index-table'),
            'ic-target':"#person_table",
            'ic-indicator':"#indicator",
            'ic-include':'#filter_table',
            }
        self.fields['name'].widget.attrs.update({'ic-trigger-on':'keyup changed', 'ic-trigger-delay':"250ms"})
        self.fields['name'].widget.attrs.update(common_attrs)
        self.fields['paid'].widget.attrs.update({'ic-trigger-on':'change'})
        self.fields['paid'].widget.attrs.update(common_attrs)
    
    
    def filter(self, qs):
        if len(self.cleaned_data['name']) > 0:
            qs = qs.annotate(name=Concat(F('first_name'), Value(' '), F('last_name'))
                ).filter(name__contains=self.cleaned_data['name'])
        if self.cleaned_data['paid'] is not None:
            qs = qs.filter(paid=self.cleaned_data['paid'])
        return qs
        