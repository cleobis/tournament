from django.contrib import admin

from .models import Match, MatchPerson, Bracket1Elim

# Register your models here.
# class MatchAdmin(admin.ModelAdmin):
    # model = Match
    # list_display = ['__str__', 'name', 'order']
    # list_editable = ('name', 'order',)
    
# class MatchPersonAdmin(a dmin.ModelAdmin):
#     model = MatchPerson
#
# class Bracket1ElimAdmin(admin.ModelAdmin):
#     model = Bracket1Elim
    
admin.site.register(Match)
admin.site.register(MatchPerson)
admin.site.register(Bracket1Elim)
# admin.site.register(Division, DivisionAdmin)