from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.core.urlresolvers import reverse
from django.http.response import HttpResponseRedirect

import math

from .models import KumiteElim1Bracket, KumiteMatch, KumiteMatchPerson
from .forms import KumiteMatchCombinedForm, KumiteMatchForm, KumiteMatchPersonForm

class BracketGrid():
    
    def __init__(self, bracket, consolation=False):
        self.bracket = bracket
        self.consolation = consolation
        if self.consolation:
            self.n_row = 2
            self.n_col = 2
        else:
            self.n_row = int(math.pow(2, self.bracket.rounds))
            self.n_col = self.bracket.rounds + 1

    
    def headers(self):
        for i in range(self.n_col-1):
            yield "Round " + str(i+1)
        yield "Winner"
    
    
    def rows(self):
        yield from [self.row(i) for i in range(self.n_row)]
    
    
    def get_match(self, round, match_i):
        if not self.consolation:
            return self.bracket.get_match(round, match_i)
        else:
            if round != 0 or match_i != 0:
                ValueError("Only one consolation match.")
            return self.bracket.consolation_match
    
    
    def row(self, row):
        
        for col in range(self.n_col - 1):
            round = self.n_col - col - 2
            span = math.pow(2, col)
            if not (row / span).is_integer():
                yield None
            else:
                match_i = row // span // 2
                match = self.get_match(round, match_i)
                
                if row / span % 2 == 0:
                    is_aka = True
                    p = match.aka if match is not None else None
                else:
                    is_aka = False
                    p = match.shiro if match is not None else None
                yield {'match_i': match_i, 'match': match, 'round': round, 'span': span, 'person': p, 'is_aka': is_aka}
        
        if row == 0:
            if self.consolation:
                match = self.bracket.consolation_match
            else:
                match = self.bracket.final_match
            yield {'match_i': 0, 'match': match, 'round': -1, 'span': self.n_row, 'person': match.winner()}
        else:
            yield None


def test_bracket(request):
    bracket = KumiteElim1Bracket.objects.all()[0]
    context = {'bracket': bracket, 'grid': BracketGrid(bracket), 'consolation_grid': BracketGrid(bracket, consolation=True)}
    return render(request, "kumite/bracket.html", context)


class KumiteMatchUpdate(UpdateView):
    model = KumiteMatch
    form_class = KumiteMatchCombinedForm
    
    
    def get_form_kwargs(self):
        kwargs = super(KumiteMatchUpdate, self).get_form_kwargs()
        kwargs.update(instance={
            'match': self.object,
            'aka': self.object.aka,
            'shiro': self.object.shiro,
        })
        # raise Exception(kwargs.__str__())
        return kwargs
    
    
    def get_success_url(self):
        
        return reverse('bracket')
    
        