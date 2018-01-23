from abc import ABC, abstractmethod
from datetime import datetime

from django.db import models
from django.core.urlresolvers import reverse
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from constance import config
from djchoices import DjangoChoices, ChoiceItem
from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class Event(models.Model):
    """The events at the tournament in which you can compete. E.g. Kata or Kumite."""
    
    class EventFormat(DjangoChoices):
        kata = ChoiceItem("A")
        elim1 = ChoiceItem("B")
    
    
    name = models.CharField(max_length=100)
    format = models.CharField(max_length=1, choices=EventFormat.choices)
    
    
    def __str__(self):
        return self.name
    
    
    def save(self):
        self.full_clean() # Catch blank strings when creating objects manually.
        super().save()
    
    
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


# class AbstractFormat(ABC):
#
#     @abstractmethod
#     def build(self, people):
#         pass
#
#     @abstractmethod
#     def asdf(self):
#         pass
#
#     @property
#     @abstractmethod
#     def winners(self):
#         pass


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
        ordering = ['start_age', 'start_rank', 'event']
    
    def __str__(self):
        if self.name:
            return "{} - {}".format(self.event, self.name)
        else:
            return "{} - Age {}-{}, {}-{}, {}".format(self.event, self.start_age,
                self.stop_age, self.start_rank.name, self.stop_rank.name, self.get_gender_display())
    
    
    def get_absolute_url(self):
        return reverse('registration:division-detail', args=[self.id,])
    
    
    def claim(self):
        "Put people into this division."
        links = EventLink.objects.filter(person__age__gte=self.start_age,
            person__age__lte=self.stop_age,
            person__rank__order__gte=self.start_rank.order,
            person__rank__order__lte=self.stop_rank.order,
            event=self.event)
        if self.gender == 'MF':
            pass
        elif self.gender in ('M', 'F', ):
            links = links.filter(person__gender=self.gender)
        else:
            raise Exception("Unexpected gender '{}' in Division {}.".format(self.gender, self.id))
        links.update(division=self)
    
    
    def save(self, *args, **kwargs):
        super(Division, self).save(*args, **kwargs)
        Division.claim_all()
    
    
    @staticmethod
    def claim_all():
        EventLink.objects.filter(person__isnull=False).update(division=None)
        for d in Division.objects.all():
            d.claim()
    
    
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
        
        people = self.eventlink_set.all()
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
def Division_post_delete(sender, instance, **kwargs):
    
    # Remove manually added people since we can't automatically assign them to a division.
    el = EventLink.objects.filter(division=instance, person__isnull=True)
    el.delete()


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
    parent = models.CharField(max_length=100, blank=True)
    
    events = models.ManyToManyField(Event, through='EventLink', related_name='person2')
    
    reg_date = models.DateTimeField('Date registered', default = datetime.now)
    paid = models.BooleanField(default=False)
    paidDate = models.DateField('Date paid', blank=True, null=True)
    
    notes = models.TextField(max_length=512, blank=True)
    
    
    class Meta:
        ordering = ['last_name', 'first_name']
    
    def full_name(self):
        return self.first_name + " " + self.last_name
    
    
    def __str__(self):
        return self.full_name()
    
    def get_absolute_url(self):
        return reverse('registration:detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        super(Person, self).save(*args, **kwargs)
        for el in self.eventlink_set.all():
            el.update_division()
            el.save()


class EventLink(models.Model):
    """A person participating in a Division.
    
    If a person participates in multiple divisions, there will be multiple EventLinks.
    
    Usually an EventLink links back to a Person registration. To support less 
    sophisticated configurations or persons registering at ring-side, the
    EventLink may be created with only a name (manual_name) and no linked
    Person.
    """
    
    person = models.ForeignKey(Person, on_delete=models.CASCADE, blank=True, null=True)
    manual_name = models.CharField(max_length=100, blank=True)
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, blank=True, null=True)
    
    
    class Meta:
        ordering = ('event__name',)
    
    
    def __str__(self):
        div = self.division.event.name if self.division is not None else "No division"
        return self.name + " - " + div
    
    
    def save(self, *args, **kwargs):
        self.update_division()
        super(EventLink, self).save(*args, **kwargs)
    
    
    def update_division(self):
        if self.person is not None:
            self.division = Division.find_eventlink_division(self)
    
    
    @property
    def is_manual(self):
        return self.person is None
    
    
    @property
    def name(self):
        return str(self.person) if not self.is_manual else self.manual_name


def create_divisions():

    ages = [6, 9, 14, 18, 31, 100]
    kata = Event.objects.get(name='Kata')
    kumite = Event.objects.get(name='Kumite')
    def ranks():
        starts = [-9, -6, -4, 1, 11]
        for i in range(len(starts)-1):
            r1 = starts[i]
            r2 = starts[i+1]-1
            if r2 == 0:
                r2 -= 1
            yield (Rank.objects.get(order=r1), Rank.objects.get(order=r2))
    
    for ia in range(len(ages)-1):
        for r1, r2 in ranks():
            d = Division(event=kata, gender='MF', start_rank=r1, stop_rank=r2, start_age=ages[ia], stop_age=ages[ia+1]-1)
            d.save()
            d = Division(event=kumite, gender='M', start_rank=r1, stop_rank=r2, start_age=ages[ia], stop_age=ages[ia+1]-1)
            d.save()
            d = Division(event=kumite, gender='F', start_rank=r1, stop_rank=r2, start_age=ages[ia], stop_age=ages[ia+1]-1)
            d.save()


def import_registrations(f):
    """Import registration data from Google Forms csv.
    
    Usage
        f = open('my_data.csv', newline='')
        import_registrations(f)
    
    The date of the last registration is cached in the SIGNUP_IMPORT_LAST_TSTAMP 
    setting to make it safe to repeatedly import the same data without creating
    duplicate registrations.
    
    Input stream should be opened with newline='' or muti-line entries will not be parsed correctly.
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
        'email'         : R('Email Address',),
        'parent'        : R('Name of parent or guardian (competitors under 18 years)'),
        'events'        : R('Events',),
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
    t_max = t_min
    for row in c:
        tstamp = datetime.datetime.strptime(row[csv_map['tstamp'].name], '%m/%d/%Y %H:%M:%S')
        if tstamp <= t_min:
            continue
        t_max = max(t_max, tstamp)
        p = Person()
        events = []
        for (field,field_info) in csv_map.items():
            v = row[field_info.name]
            if field == 'rank':
                v = Rank.parse(v)
            elif field == 'events':
                events = [Event.objects.get(name=e) for e in v.split(", ")]
                continue
            elif field == 'reg_date':
                v = tstamp
            else:
                pass
            setattr(p, field, v)
        
        p.save()
        for e in events:
            el = EventLink(person=p,event=e)
            el.save()
    config.SIGNUP_IMPORT_LAST_TSTAMP = t_max
