from django.shortcuts import render

import math

from .models import Bracket1Elim, Match

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
                match = self.bracket.get_match(round, match_i)
                
                if row / span % 2 == 0:
                    is_aka = True
                    p = match.aka if match is not None else None
                else:
                    is_aka = False
                    p = match.shiro if match is not None else None
                yield {'match_i': match_i, 'match': match, 'round': round, 'span': span, 'person': p, 'is_aka': is_aka}
        
        if row == 0:
            yield {'name': 'winner', 'match_i': 0, 'match': self.bracket.final_match, 'round': 0, 'span': self.n_row}
        else:
            yield None

# Create your views here.
def test_bracket(request):
    bracket = Bracket1Elim.objects.all()[0]
    context = {'bracket': bracket, 'grid': BracketGrid(bracket), 'consolation_grid': BracketGrid(bracket, consolation=True)}
    return render(request, "bracket/bracket.html", context)