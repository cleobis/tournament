from django.contrib import admin

from .models import Scoring, KataMatch, KataRound, KataBracket

# Register your models here.
admin.site.register(Scoring)
admin.site.register(KataMatch)
admin.site.register(KataRound)
admin.site.register(KataBracket)