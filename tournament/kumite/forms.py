from django import forms
from django.core.urlresolvers import reverse
from django.core.exceptions import ValidationError

from betterforms.multiform import MultiModelForm

from .models import KumiteMatch, KumiteMatchPerson


class KumiteMatchPersonForm(forms.ModelForm):
    class Meta:
        model = KumiteMatchPerson
        fields = ['points', 'warnings', 'disqualified'] # name


class KumiteMatchForm(forms.ModelForm):
    class Meta:
        model = KumiteMatch
        fields = ['done', 'aka_won']


class KumiteMatchCombinedForm(MultiModelForm):
    form_classes = {
        'aka': KumiteMatchPersonForm,
        'shiro': KumiteMatchPersonForm,
        'match': KumiteMatchForm,   # Must be last so its save() is called last.
    }
    
    
    def __init__(self, read_only=False, **kwargs):
        self.read_only = read_only
        super().__init__(**kwargs)
    
    def clean(self):
        super(KumiteMatchCombinedForm, self).clean()
        
        if (self.read_only):
            raise ValidationError('Can\'t save manual form.')
        
        # Determine match.done from which button was clicked
        if 'btn_done' in self.data:
            done = True
        elif 'btn_not_done' in self.data:
            done = False
        else:
            raise ValidationError('Unexpected submit button.', code='done_missing')
        self['match'].cleaned_data['done'] = done
        self['match'].instance.done = done
        
        # Determine who won
        if done:
            try:
                self['match'].instance.infer_winner()
            except ValueError as err:
                raise ValidationError(*err.args, code="infer_winer")
            self['match'].cleaned_data['aka_won'] = self['match'].instance.aka_won


class KumiteMatchPersonSwapForm(forms.Form):
    src = forms.ModelChoiceField(queryset=KumiteMatchPerson.objects.none(), widget=forms.HiddenInput())
    tgt = forms.ModelChoiceField(queryset=KumiteMatchPerson.objects.none(), widget=forms.HiddenInput())
    prefix = 'swap'
    
    def __init__(self, bracket=None, **kwargs):
        
        if bracket is None:
            raise ValueError('bracket is required.')
        self.bracket = bracket
        
        super().__init__(**kwargs)
        
        people = self.bracket.get_swappable_match_people()
        self.fields['src'].queryset = people
        self.fields['tgt'].queryset = people
    
    
    def clean(self):
        import logging
        log = logging.getLogger()
        
        if 'src' not in self.cleaned_data or 'tgt' not in self.cleaned_data:
            return
        
        if (self.cleaned_data['src'].kumitematch.bracket != self.bracket
                or self.cleaned_data['tgt'].kumitematch.bracket != self.bracket):
            raise forms.ValidationError("Person not in bracket.")
        
        if self.cleaned_data['src'] == self.cleaned_data['tgt']:
            raise forms.ValidationError("Can't swap with themselves.")
