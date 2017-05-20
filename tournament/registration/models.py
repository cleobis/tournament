from django.db import models
from datetime import date

from django.core.urlresolvers import reverse

from phonenumber_field.modelfields import PhoneNumberField

# Create your models here.

class Event(models.Model):
    """The events at the tournament in which you can compete. E.g. Kata or Kumite."""
    
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Rank(models.Model):
    order = models.SmallIntegerField()
    name = models.CharField(max_length=100)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return self.name
    

class Division(models.Model):
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    gender = models.CharField(max_length=2, choices=(('M', 'Male'), ('F', 'Female'), ('MF', 'Combined')))
    start_age = models.PositiveSmallIntegerField()
    stop_age = models.PositiveSmallIntegerField()
    start_rank = models.ForeignKey(Rank, on_delete=models.PROTECT, related_name='+')
    stop_rank = models.ForeignKey(Rank, on_delete=models.PROTECT, related_name='+')
    
    def __str__(self):
        return "{} - Age {}-{}, {}-{}".format(self.event, self.start_age,
            self.stop_age, self.start_rank.name, self.stop_rank.name)
    
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
        EventLink.objects.update(division=None)
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


class Person(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=1, choices=(('M', 'Male'), ('F', 'Female'),))
    age = models.PositiveSmallIntegerField()
    rank = models.ForeignKey(Rank, on_delete=models.PROTECT)
    instructor = models.CharField(max_length=200)
    phone_number = PhoneNumberField()
    # address
    email = models.EmailField(blank=True)
    
    events = models.ManyToManyField(Event, through='EventLink', related_name='person2')
    
    reg_date = models.DateField('Date registered', default = date.today)
    paid = models.BooleanField(default=False)
    paidDate = models.DateField('Date paid', blank=True, null=True)
    
    notes = models.TextField(max_length=512, blank=True)
    
    
    def full_name(self):
        return self.first_name + " " + self.last_name
    
    
    def __str__(self):
        return self.full_name()
    
    def get_absolute_url(self):
        return reverse('detail', kwargs={'pk': self.pk})
    
    def save(self, *args, **kwargs):
        super(Person, self).save(*args, **kwargs)
        for el in self.eventlink_set.all():
            el.update_division()
            el.save()


class EventLink(models.Model):
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.PROTECT)
    division = models.ForeignKey(Division, on_delete=models.SET_NULL, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        self.update_division()
        super(EventLink, self).save(*args, **kwargs)
    
    def update_division(self):
        self.division = Division.find_eventlink_division(self)
