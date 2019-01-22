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
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "team":
            qs = EventLink.objects.all()
            if request.object is not None:
                qs = qs.filter(division=request.object, is_team=True)
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class RankAdmin(admin.ModelAdmin):
    model = Rank
    list_display = ['__str__', 'name', 'order']
    list_editable = ('name', 'order',)


class DivisionAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'num_participants', 'event', 'gender', 'start_age', 'stop_age', 'start_rank', 'stop_rank']
    list_editable = ['event', 'gender', 'start_age', 'stop_age', 'start_rank', 'stop_rank']
    list_filter = ['event', 'gender', 'start_age', 'start_rank']
    inlines = (PersonInline,)
    
    
    def num_participants(self, obj):
        return obj.num_participants
    num_participants.short_description = "No. of participants"
    
    
    def get_queryset(self, request):
        qs = super(DivisionAdmin, self).get_queryset(request)
        return qs.annotate(num_participants=models.Count('eventlink'))
        
    def get_form(self, request, obj=None, **kwargs):
        # just save obj reference for future processing in Inline
        request.object = obj
        return super().get_form(request, obj, **kwargs)


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