from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError
# Create your models here.


def validate_score(score):
    if score < 0 or score > 10:
        raise ValidationError('{} is not a number between 0 and 10.'.format(score))

class Scoring(models.Model):
    name = models.CharField(max_length=200)
    score1 = models.FloatField(validators=[validate_score,])
    score2 = models.FloatField(validators=[validate_score,])
    score3 = models.FloatField(validators=[validate_score,])
    score4 = models.FloatField(validators=[validate_score,])
    score5 = models.FloatField(validators=[validate_score,])
    combined_score = models.FloatField(editable=False) # Will be populated by save()
    tie_score = models.FloatField(editable=False) # Will be populated by save()
    
    class Meta:
        ordering = ['-combined_score', '-tie_score']
    
    def get_score(self, i):
        return getattr(self, "score" + str(i))
    
    def get_scores(self):
        return (self.score1, self.score2, self.score3, self.score4, self.score5)
    
    def calc_combined_score(self):
        scores = self.get_scores()
        return (sum(scores) - max(scores) - min(scores)) / (len(scores) - 2)
    
    def calc_tie_score(self):
        scores = self.get_scores()
        return sum(scores) / len(scores)
    
    def save(self, *args, **kwargs):
        self.combined_score = self.calc_combined_score()
        self.tie_score = self.calc_tie_score()
        super(Scoring, self).save(*args, **kwargs)
    
    def diff(self, other):
        d = self.combined_score - other.combined_score
        if d == 0:
            d = self.tie_score - other.tie_score
        return d
    
    def __eq__(self, other):
        return self.diff(other) == 0
    
    def __lt__(self, other):
        return self.diff(other) < 0
    
    def __le__(self, other):
        return self.diff(other) <= 0
    
    def __gt__(self, other):
        return self.diff(other) > 0
    
    def __ge__(self, other):
        return self.diff(other) >= 0