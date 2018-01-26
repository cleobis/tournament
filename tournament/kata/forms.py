from django import forms

from registration.models import EventLink
from .models import KataMatch


class KataMatchForm(forms.ModelForm):
    class Meta:
        model = KataMatch
        fields = ['score1', 'score2', 'score3', 'score4', 'score5']
    
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        self.fields['score1'].widget.attrs.update({'autofocus': 'autofocus'})
    
    def clean(self):
        cleaned_data = super().clean()
        
        if self.instance.round.locked:
            raise forms.ValidationError("Round is locked.")
        
        # Determine match.done from which button was clicked
        if 'save' in self.data:
            pass
        elif 'clear' in self.data:
            for x in ('score'+str(i) for i in range(1,5+1)):
                cleaned_data[x] = None
        else:
            raise forms.ValidationError('Unexpected submit button.', code='done_missing')
        
        # Check that they filled all or none of the scores
        scores = [cleaned_data['score'+str(i)] for i in range(1,5+1)]
        if scores.count(None) not in (0, 5):
            raise forms.ValidationError("Set either all or none of the scores.")
        
        return cleaned_data


class KataBracketAddPersonForm(forms.ModelForm):
    class Meta:
        model = EventLink
        fields = ['manual_name']
     
    existing_eventlink = forms.ModelChoiceField(label="Registered late arrival", 
        queryset=EventLink.objects.none(), required=False)
    
    def __init__(self, division=None, **kwargs):
        
        if division is None:
            raise ValueError('Division is required.')
        if 'instance' in kwargs:
            instance = kwargs['instance']
        else:
            instance = EventLink()
        instance.division = division
        instance.event = division.event
        kwargs.update(instance=instance)
        
        super().__init__(**kwargs)
        
        division = self.instance.division
        people = division.eventlink_set.filter(katamatch=None)
        self.fields['existing_eventlink'].queryset = people
    
    
    def clean(self):
        if not self.cleaned_data['manual_name'] and not self.cleaned_data['existing_eventlink']:
            raise forms.ValidationError("Specify either manual name or select from menu.")