from django.contrib import admin
from django.forms import CheckboxSelectMultiple
from django.db import models

# Register your models here.
from .models import Person, Rank, Division, Event, EventLink



def get_age(obj):
    return obj.person.age

class PersonInline(admin.TabularInline):
    model = EventLink
    extra = 0
    readonly_fields = ['person', 'event']
#    fields = ['person', ]#get_age]
    
#    def get_age(self, obj):
#        return obj.person.age


class RankAdmin(admin.ModelAdmin):
    model = Rank
    list_display = ['__str__', 'name', 'order']
    list_editable = ('name', 'order',)


class DivisionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'event', 'gender', 'start_age', 'stop_age', 'start_rank', 'stop_rank', 'num_participents']
    list_editable = ['event', 'gender', 'start_age', 'stop_age', 'start_rank', 'stop_rank']
    list_filter = ['event']
    inlines = (PersonInline,)
    
    
    def num_participents(self, obj):
        return obj.num_participents
    num_participents.short_description = "No. of participents"
    
    
    def get_queryset(self, request):
        qs = super(DivisionAdmin, self).get_queryset(request)
        return qs.annotate(num_participents=models.Count('eventlink'))


class DivisionInline(admin.TabularInline):
    model = EventLink
    extra = 1


class PersonAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'gender', 'age', 'rank', 'paid']
    list_filter = ['gender', 'age', 'rank', 'paid']
    formfield_overrides = {
        models.ManyToManyField: {'widget': CheckboxSelectMultiple},
    }
    inlines = (DivisionInline,)
    search_fields = ('first_name', 'last_name', 'instructor', )



admin.site.register(Person, PersonAdmin)
admin.site.register(Rank, RankAdmin)
admin.site.register(Event)
admin.site.register(Division, DivisionAdmin)