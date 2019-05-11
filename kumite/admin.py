from django.contrib import admin
from django import forms
from django.db.models import Q

from .models import KumiteMatch, KumiteMatchPerson, KumiteElim1Bracket, Kumite2PeopleBracket, KumiteRoundRobinBracket

# Register your models here.
class KumiteMatchAdmin(admin.TabularInline):
    model = KumiteMatch
    fields = ('round', 'order', 'aka', 'shiro', 'done', 'aka_won', 'winner_match', 'consolation_match', )
    extra = 0
    
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
       if db_field.name in ("aka", "shiro", ):
           kwargs["queryset"] = KumiteMatchPerson.objects.filter(
               Q(**{"match_aka__" + request.bracket.kumite_match_bracket_field: request.bracket})
               | Q(**{"match_shiro__" + request.bracket.kumite_match_bracket_field: request.bracket})
               )
       elif db_field.name in ("winner_match", "consolation_match", ):
           kwargs["queryset"] = KumiteMatch.objects.filter(
               **{request.bracket.kumite_match_bracket_field: request.bracket}
               )
           
       return super().formfield_for_foreignkey(db_field, request, **kwargs)


class AbstractKumiteBracketAdmin(admin.ModelAdmin):
    list_display = ['division']
    
    inlines = [KumiteMatchAdmin, ]
    
    def get_form(self, request, obj=None, **kwargs):
        request.bracket = obj
        return super().get_form(request, obj, **kwargs)


class KumiteElim1BracketAdmin(AbstractKumiteBracketAdmin):
    model = KumiteElim1Bracket


class KumiteRoundRobinBracketAdmin(AbstractKumiteBracketAdmin):
    model = KumiteRoundRobinBracket
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if db_field.name in ("gold", "silver", "bronze", ):
            kwargs["queryset"] = request.bracket.division.eventlink_set.all()
           
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class Kumite2PeopleBracketAdmin(AbstractKumiteBracketAdmin):
    model = Kumite2PeopleBracket
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if db_field.name in ("winner", "loser", ):
            kwargs["queryset"] = request.bracket.division.eventlink_set.all()
           
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    


class KumiteBracketListFilter(admin.SimpleListFilter):
    parameter_name = 'bracket'
    title = 'Bracket'
    
    def lookups(self, request, model_admin):
        import heapq
        import itertools
        
        all_brackets = heapq.merge( # Merge sorted lists
            KumiteElim1Bracket.objects.all(),
            KumiteRoundRobinBracket.objects.all(),
            Kumite2PeopleBracket.objects.all(),
            key=lambda x: str(x)
            )
        return itertools.chain(
                (("None", "None"), ), 
                ((b.kumite_match_bracket_field + "=" + str(b.id), str(b)) for b in all_brackets)
            )
        return (
            ('a', 'b')
        )
    
    
    def queryset(self, request, queryset):
        if self.value() is None:
            return queryset
        elif self.value() == "None":
            return queryset.filter(bracket_2people__isnull=True, bracket_rr__isnull=True, bracket_elim1__isnull=True)
        else:
            parts = self.value().split('=')
            return queryset.filter(**{parts[0]: parts[1]})


class KumiteMatchPersonAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'eventlink', 'match_aka', 'match_shiro', 'points', 'warnings', 'disqualified']


# class KumiteMatchPersonInline(admin.TabularInline):
    # model = KumiteMatchPerson
    

class KumiteMatchAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'bracket', 'round', 'order', 'aka', 'shiro', 'done', 'aka_won')
    list_filter = (KumiteBracketListFilter, )
    # inlines = (KumiteMatchPersonInline,)
    
    
    def get_form(self, request, obj=None, **kwargs):
        request.bracket = obj.bracket if obj is not None else None
        return super().get_form(request, obj, **kwargs)
    
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        
        if db_field.name in ("aka", "shiro", ):
            kwargs["queryset"] = KumiteMatchPerson.objects.filter(
                Q(**{"match_aka__" + request.bracket.kumite_match_bracket_field: request.bracket})
                | Q(**{"match_shiro__" + request.bracket.kumite_match_bracket_field: request.bracket})
                )
        elif db_field.name in ("winner_match", "consolation_match", ):
            kwargs["queryset"] = KumiteMatch.objects.filter(
                **{request.bracket.kumite_match_bracket_field: request.bracket}
                )
           
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


admin.site.register(KumiteMatch, KumiteMatchAdmin)
admin.site.register(KumiteMatchPerson, KumiteMatchPersonAdmin)
admin.site.register(KumiteElim1Bracket, KumiteElim1BracketAdmin)
admin.site.register(Kumite2PeopleBracket, Kumite2PeopleBracketAdmin)
admin.site.register(KumiteRoundRobinBracket, KumiteRoundRobinBracketAdmin)
