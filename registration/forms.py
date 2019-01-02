from django import forms
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.db.models import F, Q, Value
from django.db.models.functions import Concat

from .models import Person, Rank, EventLink


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'gender', 'age', 'rank', 'instructor', 'phone_number', 'email', 'parent', 'confirmed', 'paid', 'events', 'notes']
        widgets = {
            'events': forms.CheckboxSelectMultiple(),
        }


class PersonCheckinForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['confirmed']


class PersonPaidForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['paid']


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
        if self.division.get_format() is not None:
            raise ValidationError('Division already created.')
        
        self.instance.event = self.division.event
        self.instance.division = self.division


class TeamAssignForm(forms.Form):
    src = forms.ModelChoiceField(queryset=EventLink.objects.none(), widget=forms.HiddenInput())
    tgt = forms.ModelChoiceField(queryset=EventLink.objects.none(), widget=forms.HiddenInput(), required=False)
    prefix = 'assign'
    
    def __init__(self, division=None, **kwargs):
        
        if division is None:
            raise ValueError('Division is required.')
        if not division.event.is_team:
            raise ValueError('Division not for teams.')
        self.division = division
        
        super().__init__(**kwargs)
        
        self.fields['src'].queryset = self.division.get_non_team_eventlinks()
        self.fields['tgt'].queryset = self.division.eventlink_set.all()
    
    
    def clean_src(self):
        # This should never actually get used because the get_swappable_match_people() queryset limits the choices.
        value = self.cleaned_data['src']
        if value.division != self.division:
            raise forms.ValidationError("Can't be assigned.")
        return value
    
    
    def clean_tgt(self):
        # This should never actually get used because the get_swappable_match_people() queryset limits the choices.
        value = self.cleaned_data['tgt']
        if value is not None:
            if value.division != self.division:
                raise forms.ValidationError("Can't be assigned.")
        return value
    
    
    def clean(self):
        super().clean()
        
        if self.division.get_format() is not None:
            raise ValidationError('Division already created.')


class PersonFilterForm(forms.Form):
    name = forms.CharField(required=False)
    confirmed = forms.TypedChoiceField(required=False, choices=((None, 'Any'), (True, 'Yes'), (False, 'No'),), 
        coerce=lambda x: True if x == 'True' else False if x == 'False' else None, empty_value=None)
    paid = forms.TypedChoiceField(required=False, choices=((None, 'Any'), (True, 'Yes'), (False, 'No'),), 
        coerce=lambda x: True if x == 'True' else False if x == 'False' else None, empty_value=None)
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        common_attrs = {'ic-get-from':reverse('registration:index-table'),
            'ic-target':"#person_table",
            'ic-indicator':"#indicator",
            'ic-include':'#filter_table',
            }
        self.fields['name'].widget.attrs.update({'ic-trigger-on':'keyup', 'ic-trigger-delay':"250ms"})
        # self.fields['name'].widget.attrs.update({'ic-trigger-on':'keyup changed', 'ic-trigger-delay':"250ms"})
        self.fields['name'].widget.attrs.update(common_attrs)
        self.fields['confirmed'].widget.attrs.update({'ic-trigger-on':'change'})
        self.fields['confirmed'].widget.attrs.update(common_attrs)
        self.fields['paid'].widget.attrs.update({'ic-trigger-on':'change'})
        self.fields['paid'].widget.attrs.update(common_attrs)
    
    
    def filter(self, qs):
        if len(self.cleaned_data['name']) > 0:
            qs = qs.annotate(name=Concat(F('first_name'), Value(' '), F('last_name'))
                ).filter(name__icontains=self.cleaned_data['name'])
        if self.cleaned_data['confirmed'] is not None:
            qs = qs.filter(confirmed=self.cleaned_data['confirmed'])
        if self.cleaned_data['paid'] is not None:
            qs = qs.filter(paid=self.cleaned_data['paid'])
        return qs
        
