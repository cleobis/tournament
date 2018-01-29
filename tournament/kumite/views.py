from django.shortcuts import render
from django.views.generic import DetailView
from django.views.generic.detail import SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.core.urlresolvers import reverse, reverse_lazy
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST
from django.contrib.admin.views.decorators import staff_member_required

import math

from .models import KumiteElim1Bracket, KumiteRoundRobinBracket, Kumite2PeopleBracket, KumiteMatch, KumiteMatchPerson
from .forms import KumiteMatchCombinedForm, KumiteMatchForm, KumiteMatchPersonForm, KumiteMatchPersonSwapForm

class BracketGrid():
    
    def __init__(self, bracket, consolation=False):
        self.bracket = bracket
        self.consolation = consolation
        if self.consolation:
            self.n_row = 2
            self.n_col = 2
        else:
            self.n_row = bracket.get_num_match_in_round(self.bracket.rounds)
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
            span = int(math.pow(2, col))
            if not (row / span).is_integer():
                match = None
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
                
                yield {'match_i': match_i, 'match': match, 'round': round, 'span': span, 'person': p, 'is_aka': is_aka, 'col': col}
                
        
        if (row / span / 2).is_integer():
            span = int(math.pow(2, self.n_col - 1))
            yield {'match_i': 0, 'match': match, 'round': -1, 'span': span, 'person': match.winner(), 'col': self.n_col-1}
        else:
            yield None


class BracketDetails(DetailView):
    model = KumiteElim1Bracket
    
    
    def get_context_object_name(self, object):
        return 'bracket'
    
    
    def get_context_data(self, **kwargs):
        
        context = super().get_context_data(**kwargs)
        object = context['object']
        context.update({'grid': BracketGrid(object), 'consolation_grid': BracketGrid(object, consolation=True),
            'next': object.get_next_match(), 'on_deck': object.get_on_deck_match(),
            'delete_url': reverse('kumite:bracket-n-delete', args=[object.id]),
            'swap_form': KumiteMatchPersonSwapForm(self.object)})
        return context


@method_decorator(staff_member_required, name='dispatch')
class BracketDelete(DeleteView):
    model = KumiteElim1Bracket
    
    
    def get_success_url(self):
        return self.object.division.get_absolute_url()


class BracketRoundRobinDetails(DetailView):
    model = KumiteRoundRobinBracket
    template_name = 'kumite/kumiteelim1bracket_detail.html'
    
    
    def get_context_object_name(self, object):
        return 'bracket'
    
    
    def get_context_data(self, object):
        
        context = super().get_context_data(object=object)
        context.update({'grid': BracketGrid(object), 'consolation_grid': None,
            'next': object.get_next_match(), 'on_dect': None,
            'delete_url': reverse('kumite:bracket-rr-delete', args=[object.id])})
        return context


class BracketRoundRobinDelete(DeleteView):
    model = KumiteRoundRobinBracket
    
    
    def get_success_url(self):
        return self.object.division.get_absolute_url()


class Bracket2PeopleDetails(DetailView):
    model = Kumite2PeopleBracket
    template_name = 'kumite/kumiteelim1bracket_detail.html'
    
    
    def get_context_object_name(self, object):
        return 'bracket'
    
    
    def get_context_data(self, object):
        
        context = super().get_context_data(object=object)
        context.update({'grid': BracketGrid(object), 'consolation_grid': None,
            'next': object.get_next_match(), 'on_dect': None,
            'delete_url': reverse('kumite:bracket-2-delete', args=[object.id])})
        return context


class Bracket2PeopleDelete(DeleteView):
    model = Kumite2PeopleBracket
    
    
    def get_success_url(self):
        return self.object.division.get_absolute_url()


@method_decorator(require_POST, name='dispatch')
class KumiteMatchPersonSwapView(BracketDetails, FormView):
    form_class = KumiteMatchPersonSwapForm
    
    
    def get_context_data(self, form=None):
        context = super().get_context_data(object=self.get_object())
        context['swap_form'] = form
        return context
    
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['bracket'] = self.get_object()
        return kwargs
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
    
    
    def form_valid(self, form):
        
        import logging
        log = logging.getLogger()
        
        p1 = form.cleaned_data['src']
        m1 = p1.kumitematch
        attr1 = "aka" if p1 == m1.aka else "shiro"
        
        p2 = form.cleaned_data['tgt']
        m2 = p2.kumitematch
        attr2 = "aka" if p2 == m2.aka else "shiro"

        if m2 == m1:
            # If swapping aka and shiro on the same match, need to update same object.
            m2 = m1
        
        setattr(m2, attr2, None)
        m2.save()
        
        setattr(m1, attr1, p2)
        m1.save()
        
        setattr(m2, attr2, p1)
        m2.save()
        
        return super().form_valid(form)
    
    
    def get_success_url(self):
        return self.object.get_absolute_url()


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
        return kwargs
    
    
    def get_success_url(self):
        return self.object['match'].bracket.get_absolute_url()
    
    
    def dispatch(self, *args, **kwargs):
        if not self.get_object().is_editable():
            return HttpResponseForbidden()
        return super(KumiteMatchUpdate,self).dispatch(*args, **kwargs)


class KumiteMatchManual(FormView):
    mocel = KumiteMatch
    form_class = KumiteMatchCombinedForm
    template_name = 'kumite/kumitematch_form.html'
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update(read_only=True)
        # kwargs.update(instance={
#             'match': self.object,
#             'aka': self.object.aka,
#             'shiro': self.object.shiro,
#         })
        return kwargs