from django.db import models
from django.core import validators
from django.core.exceptions import ValidationError

from registration.models import EventLink

from more_itertools import peekable
# Create your models here.


def validate_score(score):
    if score < 0 or score > 10:
        raise ValidationError('{} is not a number between 0 and 10.'.format(score))

class Scoring(models.Model):
    name = models.CharField(max_length=200)
    score1 = models.FloatField(validators=(validate_score,))
    score2 = models.FloatField(validators=(validate_score,))
    score3 = models.FloatField(validators=(validate_score,))
    score4 = models.FloatField(validators=(validate_score,))
    score5 = models.FloatField(validators=(validate_score,))
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


class KataMatch(models.Model):
    eventlink = models.ForeignKey(EventLink)
    round = models.ForeignKey('KataRound', on_delete=models.CASCADE)
    done = models.BooleanField(default=False)
    score1 = models.FloatField(validators=(validate_score,), blank=True, null=True)
    score2 = models.FloatField(validators=(validate_score,), blank=True, null=True)
    score3 = models.FloatField(validators=(validate_score,), blank=True, null=True)
    score4 = models.FloatField(validators=(validate_score,), blank=True, null=True)
    score5 = models.FloatField(validators=(validate_score,), blank=True, null=True)
    combined_score = models.FloatField(editable=False, blank=True, null=True) # Will be populated by save()
    tie_score = models.FloatField(editable=False, blank=True, null=True) # Will be populated by save()
    
    
    class Meta:
        ordering = ['-combined_score', '-tie_score']
    
    
    @property
    def scores(self):
        return (self.score1, self.score2, self.score3, self.score4, self.score5)
    
    
    @scores.setter
    def scores(self, value):
        (self.score1, self.score2, self.score3, self.score4, self.score5) = value
    
    def save(self, *args, **kwargs):
        
        if self.round.locked:
            raise ValidationError("Can't modify match if round is locked.")
        
        scores = self.scores
        self.done = all((x is not None for x in scores))
        if self.done:
            self.combined_score = (sum(scores) - max(scores) - min(scores)) / (len(scores) - 2)
            self.tie_score = sum(scores) / len(scores)
        else:
            self.combined_score = None
            self.tie_score = None
        
        super().save(*args, **kwargs)
        
        self.round.match_callback(self)
    
    
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
    

class KataRound(models.Model):
    
    class Meta:
        ordering = ['round', 'order']
    
    
    bracket = models.ForeignKey('KataBracket', on_delete=models.CASCADE)
    round = models.SmallIntegerField()
    order = models.SmallIntegerField()
    prev_round = models.ForeignKey('KataRound', blank=True, null=True)
    locked = models.BooleanField(default=False)
    n_winner_needed = models.PositiveSmallIntegerField()
    
    @property
    def done(self):
        return len(self.katamatch_set.filter(done=False)) == 0
    
    
    @property
    def started(self):
        return len(self.katamatch_set.filter(done=True)) > 0
    
    
    @property
    def matches(self):
        return self.katamatch_set.all()
    
    
    def get_next_match(self):
        matches = self.katamatch_set.filter(done=False)
        if len(matches) >= 1:
            return matches[0]
        else:
            return None
        
    def match_callback(self, match):
        
        if self.locked:
            raise ValidationError("Can't modify round if locked.")
        
        n_done = len(self.katamatch_set.filter(done=True))
        n_not_started = len(self.katamatch_set.filter(done=False))
        
        # Lock predecessor rounds
        if self.prev_round is not None:
            old_locked = self.prev_round.locked
            self.prev_round.locked = n_done > 0
            if self.prev_round.locked != old_locked:
                self.prev_round.save()
        
        # Clear child rounds. If any of them had started, we would be locked.
        children = self.kataround_set.all()
        if len(children) > 0:
            children.delete()
        
        # Spawn child rounds
        if self.done:
            batch = []
            n_winner = 0
            order = 0
            itr = peekable(self.katamatch_set.all())
            for m in itr: # Sorted already
                batch.append(m)
                next_m = itr.peek(None)
                if next_m is None or next_m < m:
                    n_winner += len(batch)
                    
                    if len(batch) == 1:
                        pass # Have winner. Don't actually care who they are.
                    else:
                        # Have tie
                        round = KataRound(bracket=self.bracket, prev_round=self, round=self.round+1, order=order, 
                            n_winner_needed=min(len(batch), self.n_winner_needed - n_winner))
                        round.save()
                        order -= 1
                        for p in batch:
                            m = KataMatch(eventlink=p.eventlink, round=round)
                            m.save()
                    del batch[:]
                    
                    if n_winner >= self.n_winner_needed:
                        break


class KataBracket(models.Model):
    
    division = models.ForeignKey('registration.Division', null=True)
    
    def __str__(self):
        return str(self.division) + " - Kata"
    
    
    @property
    def n_round(self):
        return self.kataround_set.all().aggregate(models.Max('round'))['round__max'] + 1
    
    
    @property
    def rounds(self):
        return self.kataround_set.all()
    
    
    def get_next_match(self):
        for r in self.rounds:
            match = r.get_next_match()
            if match is not None:
                return match
        return None
    
    
    def build(self, people):
        
        round = KataRound(bracket=self, round=0, order=0, n_winner_needed=min(3, len(people)))
        round.save()
        for p in people:
            m = KataMatch(eventlink=p, round=round)
            m.save()
    
    
    def get_people(self):
        # All participants are in the first round
        round = self.kataround_set.get(round=0)
        return EventLink.objects.filter(katamatch__round=round)
    
    
    def get_winners(self):
        n_round = self.n_round
        points = {p: [0] * (2*n_round + 1) for p in self.get_people()}
        n_winner = min(len(points), 3)
        matches = KataMatch.objects.filter(round__bracket=self, done=True)
        
        for m in matches:
            r = m.round.round
            points[m.eventlink][2*r] += m.combined_score
            points[m.eventlink][2*r+1] += m.tie_score
            points[m.eventlink][2*n_round] += 1
        points = [(p, score) for (p, score) in points.items() if score[-1] > 0]
        for (p, score) in points:
            del score[-1]
        points = sorted(points, key=lambda x: x[1], reverse=True)
        
        prev_score = None
        rank = 0
        n = 0
        n_tie = 0 
        winners = []
        for (p, score) in points:
            n_tie += 1
            if score != prev_score:
                rank += n_tie
                n_tie = 0
            if rank > n_winner:
                break
            winners.append((rank, p))
            n += 1
            prev_score = score

        for rank in range(n+1, n_winner+1):
            winners.append((rank, None))
        
        return winners


















