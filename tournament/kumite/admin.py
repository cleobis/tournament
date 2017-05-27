from django.contrib import admin

from .models import KumiteMatch, KumiteMatchPerson, KumiteElim1Bracket

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
    
admin.site.register(KumiteMatch)
admin.site.register(KumiteMatchPerson)
admin.site.register(KumiteElim1Bracket)
# admin.site.register(Division, DivisionAdmin)