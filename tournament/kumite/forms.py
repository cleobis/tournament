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
        'match': KumiteMatchForm,
        'aka': KumiteMatchPersonForm,
        'shiro': KumiteMatchPersonForm,
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

