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
    eventlink = models.ForeignKey('registration.EventLink', on_delete=models.PROTECT)
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
        
    round = models.SmallIntegerField()
    order = models.SmallIntegerField()
    
    bracket_elim1 = models.ForeignKey('KumiteElim1Bracket', on_delete=models.CASCADE, null=True)
    bracket_rr = models.ForeignKey('KumiteRoundRobinBracket', on_delete=models.CASCADE, null=True)
    bracket_2people = models.ForeignKey('Kumite2PeopleBracket', on_delete=models.CASCADE, null=True)
    
    winner_match = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    consolation_match = models.ForeignKey('self', blank=True, null=True, on_delete=models.SET_NULL, related_name='+')
    aka = models.OneToOneField(KumiteMatchPerson, blank=True, null=True, on_delete=models.PROTECT, related_name='match_aka')
    shiro = models.OneToOneField(KumiteMatchPerson, blank=True, null=True, on_delete=models.PROTECT, related_name='match_shiro')

    done = models.BooleanField(default=False)
    aka_won = models.BooleanField(default=False)
    
    
    def __str__(self):
        name = ""
        if self.is_final():
            name = ", final"
        elif self.is_consolation():
            name = ", consolation"
        if self.bracket.division:
            prefix = self.bracket.division.name
        else:
            prefix = ''
        return "{}, round {}, match {}{}".format(prefix, self.round, self.order, name)
    
    
    @property
    def bracket_field(self):
        fields = ('bracket_elim1', 'bracket_rr', 'bracket_2people')
        for f in fields:
            val = getattr(self, f)
            if val is not None:
                return f
        return None
    
    
    @property
    def bracket(self):
        fields = ('bracket_elim1', 'bracket_rr', 'bracket_2people')
        for f in fields:
            val = getattr(self, f)
            if val is not None:
                return val
        return None
    
    
    @bracket.setter
    def bracket(self, val):
        if val is not None:
            self.bracket_elim1 = None
            self.bracket_rr = None
            self.bracket_2people = None
        setattr(self, val.kumite_match_bracket_field, val)
    
    
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
        
        self.bracket.match_callback(self)
    
    @property
    def prev_matches(self):
        id_or_none = lambda x: x.id if x is not None else None
        return KumiteMatch.objects.filter(
                bracket_elim1__id=id_or_none(self.bracket_elim1),
                bracket_2people__id=id_or_none(self.bracket_2people)
            ).filter(
                Q(winner_match__id=self.id) | Q(consolation_match__id=self.id))


@receiver(post_delete, sender=KumiteMatch)
def kumite_match_post_delete(sender, instance, **kwargs):
    if instance.aka is not None:
        instance.aka.delete()
    if instance.shiro is not None:
        instance.shiro.delete()


class KumiteElim1Bracket(models.Model):
    
    name = models.CharField(max_length=250)
    rounds = models.PositiveSmallIntegerField(default=0)
    division = models.ForeignKey('registration.Division', on_delete=models.PROTECT, related_name='+', null=True)
    
    kumite_match_bracket_field = 'bracket_elim1'
    
    
    def __str__(self):
        s = str(self.division) if self.division is not None else "Unbound"
        return s + " - Elim 1"
    
    
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
        return reverse('kumite:bracket-n', args=[self.id])
    
    
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
                m = self.prev_match_aka(m)
            elif match_i < 2 * split:
                # want bottom
                match_i -= split
                m = self.prev_match_shiro(m)
            
            if m is None:
                break
        
        return m
    
    
    def match_callback(self, match):
        
        if match.winner_match:
            self.claim_people(match.winner_match)
        
        if match.consolation_match:
            self.claim_people(match.consolation_match)
    
    
    def claim_people(self, match):
        curr_ids = [x.id for x in match.people() if x is not None]
        attr_name = 'aka'
        for m in [self.prev_match_aka(match), self.prev_match_shiro(match)]:
            if m is not None:
                if m.done:
                    if m.winner_match == match:
                        p = m.winner()
                    elif m.consolation_match == match:
                        p = m.loser()
                else:
                    p = None
                
                curr_p = getattr(match, attr_name)
                
                if not KumiteMatchPerson.same_person(curr_p, p):
                    if match.done:
                        raise ValueError("Can't modify people if the match is done.")
                    
                    if p is not None:
                        p = KumiteMatchPerson(eventlink=p.eventlink)
                        p.save()
                    
                    setattr(match, attr_name, p)
                    match.save()
                    
                    if curr_p is not None:
                        curr_p.delete()
            
            attr_name = 'shiro'
    
    
    def prev_match_aka(self, match):
        # m = self.prev_matches.annotate(ordermod2=F('order') % 2).filter(ordermod2=0)
        m = [m for m in match.prev_matches if m.order % 2 == 0]
        if len(m) == 0:
            return None
        elif len(m) == 1:
            return m[0]
        else:
            print(str(match.order))
            for a in m:
                print(a)
            from django.core import exceptions
            raise MultipleObjectsReturned()
    
    
    def prev_match_shiro(self, match):
        # m = self.prev_matches.annotate(ordermod2=F('order') % 2).filter(ordermod2=1)
        m = [m for m in match.prev_matches if m.order % 2 == 1]
        if len(m) == 0:
            return None
        elif len(m) == 1:
            return m[0]
        else:
            raise MultipleObjectsReturned()


class Kumite2PeopleBracket(models.Model):

    division = models.ForeignKey('registration.Division', on_delete=models.PROTECT, related_name='+', null=True)
    winner = models.ForeignKey('registration.EventLink', on_delete=models.PROTECT, related_name='+', null=True)
    loser = models.ForeignKey('registration.EventLink', on_delete=models.PROTECT, related_name='+', null=True)
    
    rounds = 1
    kumite_match_bracket_field = 'bracket_2people'
    
    
    def __str__(self):
        s = str(self.division) if self.division is not None else "Unbound"
        return s + " - 2 People"
    
    
    def get_winners(self):
        return ((1, self.winner), (2, self.loser))
    
    
    def get_absolute_url(self):
        return reverse('kumite:bracket-2', args=[self.id,])
    
    
    def get_next_match(self):
        m = self.kumitematch_set.filter(done=False)
        if len(m) == 0:
            return None
        else:
            return m[0]
    
    
    def build(self, people):
        
        if len(people) != 2:
            raise ValueError("Kumite2PeopleBracket only supports 2 competetors.")
        
        for i in range(2):
            m = KumiteMatch(bracket=self, round=0, order=i)
            p = KumiteMatchPerson(eventlink=people[i % 2])
            p.save()
            m.aka = p
            p = KumiteMatchPerson(eventlink=people[(i+1) % 2])
            p.save()
            m.shiro = p
            if i == 0:
                m_prev = m
            else:
                m.save()
                m_prev.winner_match = m
                m_prev.consolation_match = m
                m_prev.save()
    
    
    def match_callback(self, match):
        # Cases
        # - First 2 matches are still in progress.
        # - First 2 matches done and no tie => assign winner.
        # - First 2 matches tied => Create new match.
        # - First 2 matches no longer tied => Delete extra match and assign winner.
        
        matches = self.kumitematch_set.all()
        p1 = matches[0].aka.eventlink
        p2 = matches[0].shiro.eventlink
        points = {p1: 0, p2: 0}
        all_done = True
        have_winner = False
        for im, m in enumerate(matches):
            all_done = all_done and m.done
            if m.done:
                points[m.aka.eventlink] += m.aka.points
                points[m.shiro.eventlink] += m.shiro.points
            
            if not all_done:
                break
            
            have_winner = points[p1] != points[p2] and im >= 1
                # Always have at least 2 rounds
            if have_winner:
                winner = p1 if points[p1] > points[p2] else p2
                loser  = p2 if points[p1] > points[p2] else p1
                for id in range(im+1, len(matches)):
                    matches[id].delete()
                break
        
        if all_done and have_winner:
            self.winner = winner
            self.loser = loser
        else:
            self.winner = None
            self.loser = None
            
            if all_done:
                # Create a tie break match
                m2 = KumiteMatch(bracket=self, round=0, order=im+1)
                p = KumiteMatchPerson(eventlink=m.shiro.eventlink)
                p.save()
                m2.aka = p
                p = KumiteMatchPerson(eventlink=m.aka.eventlink)
                p.save()
                m2.shiro = p
                m2.save()
                
                m.winner_match = m2
                m.consolation_match = m2
                m.save()
        self.save()
    
    
    def get_num_match_in_round(self, round=None):
        n = len(self.kumitematch_set.all())
        if round is None:
            # Can't pass argument from template. Return array.
            return [n]
        else:
            if round == 0:
                return n
            elif round == 1:
                return n * 2
            else:
                raise ValueError('Invalid round number {}.'.format(n))
    
    
    def get_match(self, round, match_i):
        if round != 0:
            raise ValueError("Only 1 round")
        return self.kumitematch_set.get(order=match_i)


class KumiteRoundRobinBracket(models.Model):
    # Round robin format for three people.
    
    division = models.ForeignKey('registration.Division', on_delete=models.PROTECT, related_name='+', null=True)
    gold = models.ForeignKey('registration.EventLink', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    silver = models.ForeignKey('registration.EventLink', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    bronze = models.ForeignKey('registration.EventLink', on_delete=models.PROTECT, related_name='+', null=True, blank=True)
    
    rounds = 1
    kumite_match_bracket_field = 'bracket_rr'
    
    
    def __str__(self):
        s = str(self.division) if self.division is not None else "Unbound"
        return s + " - Round Robin"
    
    
    def get_winners(self):
        
        return ((1, self.gold), (2, self.silver), (3, self.bronze))
    
    
    def get_absolute_url(self):
        return reverse('kumite:bracket-rr', args=[self.id])
    
    
    def get_next_match(self):
        raise NotImplementedError()
    
    
    def get_next_match(self):
        m = self.kumitematch_set.filter(done=False)
        if len(m) == 0:
            return None
        else:
            return m[0]
    
    
    def build(self, people):
        
        if len(people) != 3:
            raise ValueError("KumiteRoundRobinBracket only supports 3 people for now.")
        
        for i in range(len(people)):
            m = KumiteMatch(bracket=self, round=0, order=i)
            p = KumiteMatchPerson(eventlink=people[i])
            p.save()
            m.aka = p
            p = KumiteMatchPerson(eventlink=people[(i+1) % len(people)])
            p.save()
            m.shiro = p
            m.save()
    
    
    def get_people(self):
        from registration.models import EventLink
        
        matches = self.kumitematch_set.all()
        people = EventLink.objects.filter(Q(kumitematchperson__match_aka__bracket_rr=self)
            or Q(kumitematchperson__match_shiro__bracket_rr=self)).distinct()
        return people
    
    
    def match_callback(self, match):
        
        matches = self.kumitematch_set.all()
        points = {p: [0, 0] for p in self.get_people()}
        all_done = True
        for im, m in enumerate(matches):
            all_done = all_done and m.done
            if m.done:
                if m.aka_won:
                    points[m.aka.eventlink][0] += 1
                else:
                    points[m.shiro.eventlink][0] += 1
                diff = m.aka.points - m.shiro.points
                points[m.aka.eventlink][1] += diff
                points[m.shiro.eventlink][1] -= diff
            
            if not all_done:
                break
        
        if all_done:
            points = [(p, point) for p, point in points.items()]
            points = sorted(points, key=lambda x: x[1], reverse=True)
            
            
            ties = []
            ranks = (x for x in ("gold", "silver", "bronze"))
            prev_point = None
            prev_person = None
            for (p, point) in points:
                if prev_person != None:
                    if point != prev_point:
                        setattr(self, ranks.__next__(), prev_person)
                    else:
                        ties.append(p)
                
                if len(ties) > 0:
                    raise Exception("Ties not implemented.")
                
                prev_point = point
                prev_person = p
            
            setattr(self, ranks.__next__(), prev_person)
            self.save()
            
        else:
            if None in (self.gold, self.silver, self.bronze):
                self.gold = None
                self.silver = None
                self.bronze = None
                self.save()
                
        #     if all_done:
        #         # Create a tie break match
        #         m2 = KumiteMatch(bracket=self, round=0, order=im+1)
        #         p = KumiteMatchPerson(eventlink=m.shiro.eventlink)
        #         p.save()
        #         m2.aka = p
        #         p = KumiteMatchPerson(eventlink=m.aka.eventlink)
        #         p.save()
        #         m2.shiro = p
        #         m2.save()
        #
        #         m.winner_match = m2
        #         m.consolation_match = m2
        #         m.save()
        # self.save()
    
    
    def get_num_match_in_round(self, round=None):
        n = len(self.kumitematch_set.all())
        if round is None:
            # Can't pass argument from template. Return array.
            return [n]
        else:
            if round == 0:
                return n
            elif round == 1:
                return n * 2
            else:
                raise ValueError('Invalid round number {}.'.format(n))
    
    
    def get_match(self, round, match_i):
        if round != 0:
            raise ValueError("Only 1 round")
        return self.kumitematch_set.get(order=match_i)
    
    