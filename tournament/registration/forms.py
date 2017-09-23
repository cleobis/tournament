from django import forms
from django.core.exceptions import ValidationError

from .models import Person, Rank, EventLink


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'gender', 'age', 'rank', 'instructor', 'phone_number', 'email', 'events', 'notes']
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