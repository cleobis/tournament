# -*- coding: utf-8 -*-git

"""Module responsible for defining the events in which people can compete and registration. The rules used to run each
event are provided by other modules.

* An :class:`.Event` defines an area in which you can compete, e.g. Kata or Kumite.
* A :class:`.Division` defines a range of ages, belt ranks, and genders who compete against eachother in an Event.
* A :class:`.Person` stores the registration information for a competetor.
* For each Person, an :class:`.EventLink` is created for each Event in which they register.
* A :class:`.Rank` is a utility table for populating the belt rank choices.

"""

from datetime import date, datetime

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import Q, F
from django.db.models.signals import pre_delete, post_delete
from django.db.models.aggregates import Count, Max, Min
from django.db.models.functions import Lower
from django.dispatch import receiver
from django.utils import timezone
from django.urls import reverse

from constance import config
from djchoices import DjangoChoices, ChoiceItem
import dateutil.parser

# Create your models here.

class Event(models.Model):
    """The events at the tournament in which you can compete. E.g. Kata or Kumite.
    
    The events define the options that are presented to the users when they register. They also determine which the
    scoring rules used for each division.
    """
    
    class EventFormat(DjangoChoices):
        kata = ChoiceItem("A")
        elim1 = ChoiceItem("B")
    
    #: The name of the event to be displayed to users.
    name = models.CharField(max_length=100)
    #: The scoring rules used for the event.
    #: :func:get_format_class
    format = models.CharField(max_length=1, choices=EventFormat.choices)
    #: True if people participate in the division as a team rather than an individual. Typically used for team Kata.
    is_team = models.BooleanField(default=False) 
    
    
    def __str__(self):
        return self.name
    
    
    def save(self, **kwargs):
        self.full_clean() # Catch blank strings when creating objects manually.
        super().save(**kwargs)
    
    
    def get_orphan_links(self):
        return EventLink.objects.filter(event=self, division__isnull=True)
    
    
    def get_format_class(self, n_people):
        from kumite.models import KumiteElim1Bracket, KumiteRoundRobinBracket, Kumite2PeopleBracket
        from kata.models import KataBracket
        
        if self.format == self.EventFormat.kata:
            return KataBracket
        elif self.format == self.EventFormat.elim1:
            if n_people == 2:
                return Kumite2PeopleBracket
            elif n_people == 3:
                return KumiteRoundRobinBracket
            elif n_people > 3:
                return KumiteElim1Bracket
            else:
                raise Exception("Unexpected number of people {}.".format(n_people))
        else:
            raise Exception("Unexpected format.")


class Rank(models.Model):
    """A belt rank.
    
    By default, kyu grades are stored with `order` having a value of -kyu and
    dan grades are stored with `order` having a value of dan.
    
    Standard Karate ranks will be prepopulated in the database by the migration.
    """
    
    order = models.SmallIntegerField(unique=True)
    name = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name
    
    
    @staticmethod
    def get_dan(dan):
        return Rank.objects.get(order=dan)
    
    
    @staticmethod
    def get_kyu(kyu):
        return Rank.objects.get(order=-kyu)
    

    @staticmethod
    def parse(s):
        "Parse a string"
        import re

        m = re.match('.*(?:\D|^)(\d+)[a-z][a-z] kyu.*', s)
        if m is not None:
            return Rank.get_kyu(int(m.group(1)))
        
        m = re.match('.*(?:\D|^)(\d+)[a-z][a-z] dan.*', s)
        if m is not None:
            return Rank.get_dan(int(m.group(1)))
        
        raise ValueError("Invalid rank string \"{}\".".format(s))
    
    
    @staticmethod
    def build_default_fixture(stream=None):
        """Create a fixture file to populate the Rank table with default data.
        
        If no output stream is provided, the fixture data is saved to fixtures/rank.json.
        The data is loaded automatically as part of the database migration. 
        Alternatively, it can be loaded by calling::
        
            ./manage.py loaddata rank.json
        
        Args:
            stream (optional): Stream where the data will be written.
        """
        
        import json
        import os
    
        data = []
        pk = 0
    
        def suffix(i):
            if i <= 3:
                return ("st", "nd", "rd")[i-1]
            else:
                return "th"
    
        belts = ("White", "Yellow", "Orange", "Green", "Blue", "Purple", "Brown", "Brown", "Brown")
        belts = zip(belts, range(len(belts),0,-1))
        for (b, kyu) in belts:
            data.append({"model": "registration.rank", "pk": pk, "fields": {
                "order": -kyu, "name": "{} ({}{} kyu)".format(b, kyu, suffix(kyu))
            }})
            pk += 1
    
        belts = ("Shodan", "Nidan", "Sandan", "Yondan", "Godan", "Rokudan", "Shichidan", "Hachidan", "Kudan", "Jūdan")
        dan = 1
        for b in belts:
            data.append({"model": "registration.rank", "pk": pk, "fields": {
                "order": dan, "name": "{} ({}{} dan black belt)".format(b, dan, suffix(dan))
            }})
            dan += 1
            pk += 1
    
        if stream is None:
            # Get file path
            filename = os.path.realpath(__file__)
            filename = os.path.join(os.path.dirname(filename), "fixtures")
            if not os.path.isdir(filename):
                os.mkdir(filename)
    
            filename = os.path.join(filename, "rank.json")
            with open(filename, 'w') as stream:
                json.dump(data, stream, indent=4)
        else:
            json.dump(data, stream, indent=4)


class Division(models.Model):
    """A division is a group of people who will compete against eachother in a single event.
    
    
    """
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=2, choices=(('M', 'Male'), ('F', 'Female'), ('MF', 'Combined')))
    start_age = models.PositiveSmallIntegerField()
    stop_age = models.PositiveSmallIntegerField()
    start_rank = models.ForeignKey(Rank, on_delete=models.PROTECT, related_name='+')
    stop_rank = models.ForeignKey(Rank, on_delete=models.PROTECT, related_name='+')
    
    class State(DjangoChoices):
        ready = ChoiceItem("1")
        running = ChoiceItem("4")
        done = ChoiceItem("7")
    state = models.CharField(max_length=1, choices=State.choices, default=State.ready)
    
    
    class Meta:
        ordering = ['event__is_team', 'start_age', 'start_rank', 'event']
    
    def __str__(self):
        s = str(self.event) + ": "
        if self.name:
            s = s + self.name
        else:
            if self.start_age == 1 and self.stop_age == 99:
                s = s + "All Ages"
            elif self.stop_age == 99:
                s = s + str(self.start_age) + "+"
            else:
                s = s + str(self.start_age) + "-" + str(self.stop_age)
            
            s = s + ", "
            if self.start_rank == Rank.get_dan(1) and self.stop_rank == Rank.get_dan(10):
                s = s + "Black Belt"
            else:
                s = s + self.start_rank.name + " - " + self.stop_rank.name
            
            s = s + ", " + self.get_gender_display()
        
        return s
    
    
    def get_absolute_url(self):
        return reverse('registration:division-detail', args=[self.id,])
    
    
    def get_confirmed_eventlinks(self):
        """Returns the :class:`.EventLink`s that will participate in the division.
        
        For individual events, the EventLinks for confirmed people and EventLinks that are manually added are returned.
        
        For team events, the EventLinks that are teams are returned.
        """
        if self.event.is_team:
            return self.eventlink_set.filter(is_team=True)
        else:
            return self.eventlink_set.filter(Q(person__confirmed=True) | Q(person=None))
    
    
    def get_noshow_eventlinks(self):
        """Returns the :class:`.EventLink`s that will NOT participate in the division.
        
        For individual events, the EventLinks with confirmed=False are returned.
        
        For team events, the EventLinks that are not assigned to teams are returned.
        """
        if self.event.is_team:
            return self.eventlink_set.filter(team=None, is_team=False)
        else:
            return self.eventlink_set.filter(person__confirmed=False)
    
    
    def get_team_eventlinks(self):
        return self.eventlink_set.filter(is_team=True)
    
    
    def get_non_team_eventlinks(self):
        return self.eventlink_set.filter(is_team=False)
    
    
    def get_num_registered(self):
        if self.event.is_team:
            return self.get_team_eventlinks().count()
        else:
            return self.get_non_team_eventlinks().count()
    
    
    def filter_eventlinks(self):
        """Return QuerySet of :class:`.EventLink` that should be in this division."""
        links = EventLink.objects.filter(person__age__gte=self.start_age,
                                         person__age__lte=self.stop_age,
                                         person__rank__order__gte=self.start_rank.order,
                                         person__rank__order__lte=self.stop_rank.order,
                                         event=self.event,
                                         locked=False)
        if self.gender == 'MF':
            pass
        elif self.gender in ('M', 'F',):
            links = links.filter(person__gender=self.gender)
        else:
            raise Exception("Unexpected gender '{}' in Division {}.".format(self.gender, self.id))

        return links


    def claim(self):
        """Put people into this division.
        
        If all members of a team move to the same division, they stay in a team. If some of the members
        move to a new division, only the members that stay in the original division will stay in a team.
        """
        
        links = self.filter_eventlinks()
        links.exclude(division=self).update(division=self)
        
        if not self.event.is_team:
            return
        
        teams = set((x.team.id for x in links if x.team is not None))
        teams = EventLink.objects.annotate(
            min_div=Min('eventlink__division__pk'), 
            max_div=Max('eventlink__division__pk'), 
            count=Count('eventlink')
            ).filter(id__in=teams)
        
        # If everyone moved to the division, update the team
        teams.filter(min_div=self.id, max_div=self.id).update(division=self)
        
        # Split teams
        split_teams = teams.exclude(division=self)
        links.filter(team__in=split_teams).update(team=None)
    
    
    def save(self, *args, **kwargs):
        super(Division, self).save(*args, **kwargs)
        
        # Remove auto-assigned event links from division
        links = self.eventlink_set.filter(person__isnull=False, locked=False, is_team=False)
        link_ids = [x.id for x in links]
        links.update(division=None)
        
        # Add back in the event links that still fit. Also fixes teams.
        self.claim()
        
        # Links might belong in another division now
        for link in EventLink.objects.filter(division=None, id__in=link_ids):
            link.update_division()
            if link.division is not None:
                link.save()
    
    
    @property
    def status(self):
        b = self.get_format()
        if b:
            if b.get_next_match() is None:
                return "Done"
            else:
                return "Started"
        else:
            return "Ready"
    
    
    @staticmethod
    def find_eventlink_division(eventlink):
        d = Division.objects.filter(start_age__lte=eventlink.person.age,
            stop_age__gte=eventlink.person.age,
            start_rank__order__lte=eventlink.person.rank.order,
            stop_rank__order__gte=eventlink.person.rank.order,
            event=eventlink.event,
            gender__contains=eventlink.person.gender)
        if len(d) == 0:
            # clear it if it was previously set
            d = None
        elif len(d) == 1:
            d = d[0]
        else:
            # Should really do something about multiple divisions.
            d = d[0]
        return d
    
    
    def build_format(self):
        fmt = self.get_format()
        if fmt is not None:
            raise Exception("Already build.")
        
        people = self.get_confirmed_eventlinks()
        fmt = self.event.get_format_class(len(people))(division=self)
        fmt.save()
        fmt.build(people)
        return fmt
    
    
    def get_format(self):
        
        from kumite.models import KumiteElim1Bracket, KumiteRoundRobinBracket, Kumite2PeopleBracket
        from kata.models import KataBracket
        
        classes = [KumiteElim1Bracket, KumiteRoundRobinBracket, Kumite2PeopleBracket, KataBracket]
        
        for c in classes:
            fmt = c.objects.filter(division=self)
            if len(fmt) == 1:
                return fmt[0]
            elif len(fmt) > 1:
                return fmt[0] # Should really do some error handeling
        
        return None


@receiver(pre_delete, sender=Division)
def Division_pre_delete(sender, instance, **kwargs):

    # Remove manually added people and teams since we can't automatically assign them to a division.
    el = EventLink.objects.filter(division=instance, person__isnull=True)
    el.delete()


@receiver(post_delete, sender=Division)
def Division_post_delete(sender, instance, **kwargs):

    # Call claim on the orphaned people since there could be overlapping divisions. This can't be done in the
    # pre_delete handler because our changes would be overwritten.
    for el in instance.filter_eventlinks().all():
        el.update_division()
        if el.division is not None:
            el.save()


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female'),))
    age = models.PositiveSmallIntegerField()
    rank = models.ForeignKey(Rank, on_delete=models.PROTECT)
    instructor = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=200, blank=True)
    # address
    email = models.EmailField(blank=True)
    parent = models.CharField('Parent or Guardian (if under 18)', max_length=100, blank=True)
    
    events = models.ManyToManyField(Event, through='EventLink', related_name='person2')
    teammates = models.CharField(max_length=200, blank=True)
    
    reg_date = models.DateTimeField('Date registered', default = datetime.now)
    paid = models.BooleanField(default=False)
    paidDate = models.DateField('Date paid', blank=True, null=True)
    confirmed = models.BooleanField('Checked in', default=False)
    
    notes = models.TextField(max_length=512, blank=True)
    
    class Meta:
        ordering = [Lower('last_name'), Lower('first_name')]
    
    def full_name(self):
        return self.first_name + (" " if len(self.first_name) > 0 and len(self.last_name) > 0 else "") + self.last_name
    
    
    def __str__(self):
        return self.full_name()
    
    def get_absolute_url(self):
        return reverse('registration:detail', kwargs={'pk': self.pk})
    
    
    def clean(self):
        if self.age < 18 and len(self.parent) == 0:
            raise ValidationError("Parent or guardian required if under 18.")
    
    
    def save(self, *args, **kwargs):
        if self.paid and self.paidDate is None:
            self.paidDate = date.today()
            
        super(Person, self).save(*args, **kwargs)
        for el in self.eventlink_set.all():
            el.update_division()
            el.save()


class EventLink(models.Model):
    """A person participating in a :class:`.Division`.
    
    If a person participates in multiple divisions, there will be multiple EventLinks.
    
    Usually an EventLink links back to a :class:`.Person` registration. To support less 
    sophisticated configurations or persons registering at ring-side, the
    EventLink may be created with only a name (manual_name) and no linked
    Person.
    
    An EventLink can represent a team of people participating in an event. In this 
    case, there will be a EventLink for each person (with `is_team=False`), each of 
    which has a `team` field that points to a shared EventLink (with `is_team=True`).
    """
    
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    manual_name = models.CharField(max_length=100, blank=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, blank=True, null=True)
    locked = models.BooleanField(default=False)
    disqualified = models.BooleanField(default=False) # Indicates that record is a placeholder for brackets, not a real person
    is_team = models.BooleanField(default=False)
    team = models.ForeignKey('EventLink', on_delete=models.SET_NULL, blank=True, null=True)
    
    class Meta:
        ordering = ('event__name',)
    
    
    def __str__(self):
        div = self.division.event.name if self.division is not None else "No division"
        return self.name + " - " + div
    
    
    def clean(self):
        if self.person is not None and len(self.manual_name) > 0:
            raise ValidationError("Can't set both person and manual_name")
        if self.is_team and len(self.manual_name) > 0:
            raise ValidationError("Can't set manual_name for team")
        if (self.is_team or self.is_manual) and self.division is None:
            raise ValidationError("Manual and team EventLinks must have a division")
    
    
    def save(self, *args, **kwargs):
        self.update_division()
        super(EventLink, self).save(*args, **kwargs)
    
    
    def update_division(self):
        if self.person is not None and not self.locked:
            self.division = Division.find_eventlink_division(self)
    
    
    @staticmethod
    def get_disqualified_singleton(event):
        signature = {"event": event, "disqualified": True}
        el = EventLink.objects.filter(**signature)
        if len(el) > 0:
            el = el[0]
        else:
            el = EventLink(**signature, manual_name="DISQUALIFIED", locked=True)
            el.save()
        return el
    
    
    @staticmethod
    def no_division_eventlinks():
        return EventLink.objects.filter(division=None, disqualified=False)
    
    
    @property
    def is_manual(self):
        return len(self.manual_name) > 0
    
    
    @property
    def name(self):
        if self.is_manual:
            return self.manual_name
        elif self.is_team:
            names = [x.name for x in self.eventlink_set.all()]
            names.sort()
            if len(names) == 0:
                return "Empty team"
            if len(names) == 1:
                return "Team " + names[0]
            else:
                s = ", ".join(names[0:-1])
                s = " and ".join([s, names[-1]])
                return "Team " + s
        elif self.person is not None:
            return str(self.person)
        else:
            # Should never happen
            return "Unknown"


def create_divisions():

    
    try:
        kata = Event.objects.get(name='Kata')
    except Event.DoesNotExist:
        kata = Event.objects.create(name='Kata', format=Event.EventFormat.kata)
        
    try:
        kumite = Event.objects.get(name='Kumite')
    except Event.DoesNotExist:
        kumite = Event.objects.create(name='Kumite', format=Event.EventFormat.elim1)
    
    def ranks(starts):
        for i in range(len(starts)-1):
            r1 = starts[i]
            r2 = starts[i+1]-1
            if r2 == 0:
                r2 -= 1
            yield (Rank.objects.get(order=r1), Rank.objects.get(order=r2))
    
    rank_starts = [-9, -6, -4, 1, 11]
    ages = [1, 11, 15, 18, 100]
    for ia in range(len(ages)-1):
        for r1, r2 in ranks(rank_starts):
            d = Division(event=kata, gender='MF', start_rank=r1, stop_rank=r2, start_age=ages[ia], stop_age=ages[ia+1]-1)
            d.save()
            d = Division(event=kumite, gender='M', start_rank=r1, stop_rank=r2, start_age=ages[ia], stop_age=ages[ia+1]-1)
            d.save()
            d = Division(event=kumite, gender='F', start_rank=r1, stop_rank=r2, start_age=ages[ia], stop_age=ages[ia+1]-1)
            d.save()
    
    try:
        team_kata = Event.objects.get(name='Team kata')
    except Event.DoesNotExist:
        team_kata = Event.objects.create(name='Team kata', format=Event.EventFormat.kata, is_team=True)
    
    rank_starts = [-9, -6, -4, 1, 11]
    for r1, r2 in ranks(rank_starts):
        d = Division(event=team_kata, gender='MF', start_rank=r1, stop_rank=r2, start_age=1, stop_age=99)
        d.save()


@transaction.atomic # Fail the whole import if there is a parse error
def import_registrations(f):
    """Import registration data from Google Forms csv.
    
    Usage
        f = open('my_data.csv', newline='')
        import_registrations(f)
    
    The date of the last registration is cached in the SIGNUP_IMPORT_LAST_TSTAMP 
    setting to make it safe to repeatedly import the same data without creating
    duplicate registrations.
    
    Input stream should be opened with newline='' or muti-line entries will not be parsed correctly.
    
    .. todo:: Pay attention to timezones when parsing dates. See https://docs.djangoproject.com/en/1.11/topics/i18n/timezones/
    """

    import csv
    from collections import namedtuple
    import datetime
    
    R = namedtuple('CsvMap', field_names='name')
    csv_map = {
        'tstamp'        : R('Timestamp',),
        'first_name'    : R('First Name',),
        'last_name'     : R('Last Name',),
        'gender'        : R('Gender',), # Male, Female
        'age'           : R('Age',),
        'rank'          : R('Rank',),
        'instructor'    : R('Instructor',),
        'phone_number'  : R("Phone number",),
        'email'         : R(['Email Address','Username'],),
        'parent'        : R('Name of parent or guardian (competitors under 18 years)'),
        'events'        : R('Events',),
        'teammates'     : R('Teammates for Team Kata'),
        'reg_date'      : R('Timestamp',),
        #paid = models.BooleanField(default=False)
        #paidDate = models.DateField('Date paid', blank=True, null=True)
        'notes'         : R('Notes',),
        }
        #'City': 'Cambridge'
        #'Name of parent or guardian (competitors under 18 years)': 'Ann Pratt'
        #'Address': '', 'Postal Code': 'N1R 5J8'
        #'Province': 'Ontario', 'Email': '', 'Rank': 'Purple (4th kyu)'

    c = csv.DictReader(f)
    
    t_min = config.SIGNUP_IMPORT_LAST_TSTAMP
    if timezone.is_aware(t_min):
        t_min = timezone.make_naive(t_min)
    t_max = t_min
    added = 0
    skipped = 0
    line = 1 # Since first row is header
    for row in c:
        
        line += 1
        err_str = " while parsing line {}:\n{}".format(line, row)
        
        # Parse datestamp.
        tstamp = dateutil.parser.parse(row[csv_map['tstamp'].name])
        if timezone.is_aware(tstamp):
            tstamp = timezone.make_naive(tstamp)
        
        if tstamp <= t_min:
            skipped += 1
            continue
        t_max = max(t_max, tstamp)
        p = Person()
        events = []
        for (field,field_info) in csv_map.items():
            
            found = False
            field_names = field_info.name
            if isinstance(field_names, str):
                field_names = [field_names]
            for fn in field_names:
                if fn in row:
                    v = row[fn]
                    found = True
                    break
            if not found:
                if field in ('teammates',):
                    continue
                else:
                    raise ValueError('Unable to find ' + field_info.name + err_str)
            
            if field == 'rank':
                v = Rank.parse(v)
            elif field == 'events':
                # Delimiter used to be ", ", now ":"
                if ';' in v:
                    v = v.split(';')
                else:
                    v = v.split(", ")
                events = [Event.objects.get(name=e) for e in v]
                continue
            elif field == 'reg_date':
                v = tstamp
            elif field == 'gender':
                if v == 'Male':
                    v = 'M'
                elif v == 'Female':
                    v = 'F'
                else:
                    raise ValueError("Unexpected gender {}{}".format(v, err_str))
            else:
                pass
            setattr(p, field, v)
        try:
            p.full_clean()
        except ValidationError as e:
            raise ValueError("Validation error{}:\n{}".format(err_str, e))
        p.save()
        for e in events:
            el = EventLink(person=p,event=e)
            el.update_division()
            el.save()
        added += 1
    config.SIGNUP_IMPORT_LAST_TSTAMP = t_max
    
    return {"added": added, "skipped": skipped}


def export_registrations(f):
    """Export registration data as a csv file.
    
    Usage:
        with open("filename.csv", "w", newline='''') as f:
            export_registrations(f)
    """
    
    from csv import writer
    csv = writer(f)
    
    fields = ("first_name", "last_name", 'gender', 'age', 'rank', 'instructor', 'phone_number', 'email', 'parent', 'events', 'reg_date', 'notes')
    
    def process_field(p, f):
        if f == 'events':
            return ", ".join((el.event.name for el in p.eventlink_set.all()))
        else:
            return getattr(p, f)
    
    csv.writerow(fields)
    for p in Person.objects.all():
        csv.writerow((process_field(p, f) for f in fields))
    
