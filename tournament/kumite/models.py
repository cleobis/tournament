import math

from django.db import models
from django.db.models import Q, F
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.exceptions import MultipleObjectsReturned
from django.core.urlresolvers import reverse, reverse_lazy

# from registration.models import AbstractFormat

# Create your models here.

class KumiteMatchPerson(models.Model):
    eventlink = models.ForeignKey('registration.EventLink', on_delete=models.PROTECT, related_name='+')
    points = models.PositiveSmallIntegerField(default=0)
    warnings = models.PositiveSmallIntegerField(default=0)
    disqualified = models.BooleanField(default=False)
    
    
    def __str__(self):
        return self.eventlink.name
    
    
    @property
    def name(self):
        return self.eventlink.name
    
    
    @property
    def kumitematch(self):
        return KumiteMatch.objects.get(Q(aka=self.id) | Q(shiro=self.id))
    
    
    @staticmethod
    def same_person(p1,p2):
        return (p1 is None and p2 is None) or (p1 is not None and p2 is not None and p1.eventlink == p2.eventlink)


class KumiteMatch(models.Model):
    
    class Meta:
        ordering = ['-round', 'order']
    
    bracket = models.ForeignKey('KumiteElim1Bracket', on_delete=models.CASCADE)
    round = models.SmallIntegerField()
    order = models.SmallIntegerField()

    winner_match = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    consolation_match = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    aka = models.OneToOneField(KumiteMatchPerson, blank=True, null=True, on_delete=models.PROTECT, related_name='+')
    shiro = models.OneToOneField(KumiteMatchPerson, blank=True, null=True, on_delete=models.PROTECT, related_name='+')

    done = models.BooleanField(default=False)
    aka_won = models.BooleanField(default=False)
    
    
    def __str__(self):
        name = ""
        if self.is_final():
            name = ", final"
        elif self.is_consolation():
            name = ", consolation"
        return "{}, round {}, match {}{}".format(self.bracket.name, self.round, self.order, name)
    
    
    def get_absolute_url(self):
        return reverse('kumite:match', args=[self.id])
    
    
    def people(self):
        return [self.aka, self.shiro]
    
    
    def winner(self):
        if self.done:
            return self.aka if self.aka_won else self.shiro
        else:
            return None
    
    
    def infer_winner(self):
        if self.done:
            if self.aka.disqualified or self.shiro.disqualified:
                raise ValueError("Disqualifications not implemented") #################################
            if self.aka.points == self.shiro.points:
                raise ValueError("Ties not implemented") #############################################
            self.aka_won = self.aka.points > self.shiro.points
    
    
    def loser(self):
        if self.done:
            p = self.shiro if self.aka_won else self.aka
            if p.disqualified:
                return None
            return p
        else:
            return None
    
    
    def is_final(self):
        return self.round == 0 and self.order == 0
    
    
    def is_consolation(self):
        return self.round == 0 and self.order == -1
    
    
    def is_ready(self):
        """Returns true if the match is ready to be run for the first time."""
        return not self.done and self.is_editable()
    
    
    def is_editable(self):
        """Returns true if the match outcome can be changed without invalidating other completed matches."""
        return (len(self.prev_matches.filter(done=False)) == 0
            and (self.winner_match is None or not self.winner_match.done)
            and (self.consolation_match is None or not self.consolation_match.done))
    
    
    def save(self, *args, **kwargs):
        if self.done and not self.is_editable():
            raise ValueError("Can't complete match if predecessor isn't complete.")
        
        super(KumiteMatch, self).save(*args, **kwargs)
        
        if self.winner_match:
            self.winner_match.claim_people()
        
        if self.consolation_match:
            self.consolation_match.claim_people()
    
    @property
    def prev_matches(self):
        return KumiteMatch.objects.filter(bracket__id=self.bracket.id).filter(
            Q(winner_match__id=self.id) | Q(consolation_match__id=self.id))
    
    
    @property
    def prev_match_aka(self):
        # m = self.prev_matches.annotate(ordermod2=F('order') % 2).filter(ordermod2=0)
        m = [m for m in self.prev_matches if m.order % 2 == 0]
        if len(m) == 0:
            return None
        elif len(m) == 1:
            return m[0]
        else:
            print(str(self.order))
            for a in m:
                print(a)
            from django.core import exceptions
            raise MultipleObjectsReturned()
    
    
    @property
    def prev_match_shiro(self):
        # m = self.prev_matches.annotate(ordermod2=F('order') % 2).filter(ordermod2=1)
        m = [m for m in self.prev_matches if m.order % 2 == 1]
        if len(m) == 0:
            return None
        elif len(m) == 1:
            return m[0]
        else:
            raise MultipleObjectsReturned()
    
    
    def claim_people(self):
        curr_ids = [x.id for x in self.people() if x is not None]
        attr_name = 'aka'
        for m in [self.prev_match_aka, self.prev_match_shiro]:
            if m is not None:
                if m.done:
                    if m.winner_match == self:
                        p = m.winner()
                    elif m.consolation_match == self:
                        p = m.loser()
                else:
                    p = None
                
                curr_p = getattr(self, attr_name)
                
                if not KumiteMatchPerson.same_person(curr_p, p):
                    if self.done:
                        raise ValueError("Can't modify people if the match is done.")
                    
                    if p is not None:
                        p = KumiteMatchPerson(eventlink=p.eventlink)
                        p.save()
                    
                    setattr(self, attr_name, p)
                    self.save()
                    
                    if curr_p is not None:
                        curr_p.delete()
            
            attr_name = 'shiro'


@receiver(post_delete, sender=KumiteMatch)
def kumite_match_post_delete(sender, instance, **kwargs):
    if instance.aka is not None:
        instance.aka.delete()
    if instance.shiro is not None:
        instance.shiro.delete()


class KumiteElim1Bracket(models.Model):
    
    people = models.ManyToManyField(KumiteMatchPerson)
    name = models.CharField(max_length=250)
    rounds = models.PositiveSmallIntegerField(default=0)
    division = models.ForeignKey('registration.Division', on_delete=models.PROTECT, related_name='+', null=True)
    
    @property
    def final_match(self):
        m = self.kumitematch_set.filter(round=0, order=0)
        if len(m) == 0:
            return None
        elif len(m) == 1:
            return m[0]
        else:
            raise MultipleObjectsReturned('Multiple final matches.')
    
    
    @property
    def consolation_match(self):
        m = self.kumitematch_set.filter(round=0, order=-1)
        if len(m) == 0:
            return None
        elif len(m) == 1:
            return m[0]
        else:
            raise MultipleObjectsReturned('Multiple consolation matches.')
    
    
    def get_next_match(self):
        m = self.kumitematch_set.filter(done=False)
        if len(m) == 0:
            return None
        m = m[0]
        assert m.is_ready(), "Next match {} isn't ready.".format(m)
        return m
    
    
    def get_on_deck_match(self):
        m = self.kumitematch_set.filter(done=False)
        if len(m) < 2:
            return None
        return m[1]
    
    
    def get_winners(self):
        
        unwrap = lambda x: x.eventlink if x is not None else None
        return ((1, unwrap(self.final_match.winner())),
            (2, unwrap(self.final_match.loser())), 
            (3, unwrap(self.consolation_match.winner())))
    
    
    def get_absolute_url(self):
        return reverse('kumite:bracket', args=[self.id])
    
    
    def build(self, people):
        
        if len(self.kumitematch_set.all()) > 0:
            raise Exception("Bracket has already been built.")
        
        # Consolation Match
        consolation = KumiteMatch()
        consolation.bracket = self
        consolation.str = "consolation"
        consolation.round = 0
        consolation.order = -1
        consolation.save()
        
        # Build tree recursively
        def build_helper(bracket, round, match, parent, order):
            
            if len(order) > 2:
                # Add another round
                m = KumiteMatch()
                m.bracket = self
                m.str = str(round)
                m.round = round
                m.order = match
                m.winner_match = parent
                m.save()
                
                split = len(order) // 2
                build_helper(bracket, round + 1, 2 * match, m, order[:split])
                build_helper(bracket, round + 1, 2 * match + 1, m, order[split:])
                
            elif len(order) == 2:
                
                if order[1] >= len(people):
                    # Competetor gets a buy
                    m = KumiteMatchPerson(eventlink=people[order[0]])
                    m.save()
                    if match % 2 == 0:
                        parent.aka = m
                    else:
                        parent.shiro = m
                    parent.save()
                    
                else:
                    m = KumiteMatch()
                    m.bracket = self
                    m.str = str(round)
                    m.round = round
                    m.order = match
                    m.winner_match = parent
                    p = KumiteMatchPerson(eventlink=people[order[0]])
                    p.save()
                    m.aka = p
                    p = KumiteMatchPerson(eventlink=people[order[1]])
                    p.save()
                    m.shiro = p
                    m.save()
                
            else:
                raise Exception("Bracket is too big for number of participents.")
            
            if round == 1:
                # Connect consolation match
                m.consolation_match = consolation
                m.save()
            
            return m
        
        n_person = len(people)
        if n_person < 4:
            raise ValueError("Minimum 4 competetors.")
        self.rounds = math.ceil(math.log2(n_person))
        
        order = self.get_seed_order()
        round = 0
        m = build_helper(self, round, 0, None, order)
        
        self.save()
    
    
    def get_seed_order(self, rounds=None):
        """
        Returns order for assigning participants to the initial round.
        
        For example, get_seed_order(2) will return the seed orders for a 2
        round bracket (4 competetors) as [0 3 1 2]. This means that the first
        match is between competetors 0 and 4 and the second match is between 
        competetors 2 and 1.
        
        Args:
            rounds (optional): The number of rounds. Defaults to self.rounds.
        
        Returns:
            List of orders.
        """
        if rounds is None:
            rounds = self.rounds
        
        if rounds // 1 != rounds or rounds <= 0:
            raise ValueError('Rounds should be a positive integer. Got {}.'.format(rounds))
        
        order = [0, 1]
        for round in range(rounds-1):
            order = [2 * x for x in order] + [2 * x + 1 for x in reversed(order)]
        
        order = sorted(range(len(order)), key=lambda k: order[k])
        
        return order
    
    
    def get_num_match_in_round(self, round=None):
        if round is None:
            # Can't pass argument from template. Return array.
            return [ int(math.pow(2, round)) for round in range(0,self.rounds) ]
        else:
            return int(math.pow(2, round))
    
    
    def get_match(self, round, match_i):
        """
        Returns a match specified by round and match index (order).
        
        If the bracket is incomplete, some matches will not exist. In this
        case, None is returned.
        
        Args:
            round: The round index. 0 is finals, preceeding rounds are
                positive numbers.
            match_i: The match index. 0 to 2^round-1. The consolation match
                is -1 in round 0.
        
        Returns:
            The specified match or None.
        """
        #       2    1      0
        # 0      ____
        # 1          \____
        # 2 ----\____/    \
        # 3 ----/          \____
        # 4 ----\____      /
        # 5 ----/    \____/
        # 6      ____/
        # 7
        # -1                ____
        
        if round // 1 != round or round < 0 or self.rounds <= round:
            raise ValueError("Invalid round {}.".format(round))
        
        if round == 0 and match_i == -1:
            return self.consolation_match
        
        if match_i // 1 != match_i or match_i < 0 or self.get_num_match_in_round(round) <= match_i:
            raise ValueError("Invalid match index {}.".format(match_i))
            
        split = -1
        m = self.final_match
        for i_round in range(round):
            split = self.get_num_match_in_round(round - i_round - 1)
            if match_i < split:
                # want top
                m = m.prev_match_aka
            elif match_i < 2 * split:
                # want bottom
                match_i -= split
                m = m.prev_match_shiro
            
            if m is None:
                break
        
        return m

