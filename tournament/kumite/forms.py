from django import forms
from django.core.urlresolvers import reverse

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
