from django import forms

from .models import Scoring


class ScoringForm(forms.ModelForm):
    class Meta:
        model = Scoring
        fields = ['name', 'score1', 'score2', 'score3', 'score4', 'score5']

