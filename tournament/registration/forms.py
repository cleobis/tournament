from django import forms

from .models import Person, Rank


class PersonForm(forms.ModelForm):
    class Meta:
        model = Person
        fields = ['first_name', 'last_name', 'gender', 'age', 'rank', 'instructor', 'phone_number', 'email', 'events', 'notes']
        widgets = {
            'events': forms.CheckboxSelectMultiple(),
        }
