from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.core.urlresolvers import reverse_lazy, reverse
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from registration.models import EventLink

from .models import Scoring
from .forms import ScoringForm

from .models import KataBracket, KataRound, KataMatch
from .forms import KataMatchForm, KataBracketAddPersonForm

# Create your views here.

class KataScoreList(generic.ListView):
    model = Scoring

class KataScoreListWithAdd(CreateView):
    template_name = "kata/scoring_list.html"
    form_class = ScoringForm
    success_url = reverse_lazy('list')

    def get_context_data(self, **kwargs):
        context = super(KataScoreListWithAdd, self).get_context_data(**kwargs)
        context["scores"] = self.get_queryset()
        return context

    def get_queryset(self):
        return Scoring.objects.all()#

    def form_valid(self, form):
        self.object = form.save()
        return super(KataScoreListWithAdd, self).form_valid(form)

class KataScoreListModifyInline(UpdateView):
    model = Scoring
    template_name = "kata/scoring_list_update_inline.html"
    form_class = ScoringForm
    
    def get_success_url(self):
        return '/kata_score/list/inline/{}/'.format(self.object.id)
    
class KataScoreListDisplayInline(generic.DetailView):
    model = Scoring
    template_name = "kata/scoring_list_display_inline.html"
    
    
# class KataBracketList(generic.ListView):
#     model = KataBracket

class KataBracketDetails(generic.DetailView):
    model = KataBracket
    context_object_name = "bracket"
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = False
        
        context['add_form'] = KataBracketAddPersonForm(self.object.division)
        
        return context


def check_match_bracket(view, obj):
    
    bracket_id = view.kwargs.get('bracket', None)
    if bracket_id is None:
        raise AttributeError(u"Generic detail view %s must be called with "
                             u"either an object pk or a slug."
                             % view.__class__.__name__)
    bracket_id = int(bracket_id)
    view.bracket = obj.round.bracket
    if view.bracket.id != bracket_id:
        raise Http404("No KataBrackets found matching the query")
    

class KataBracketEditMatch(UpdateView):
    template_name = 'kata/katabracket_detail.html'
    model = KataMatch
    form_class = KataMatchForm
    
    
    def get_object(self, queryset=None):
        
        obj = super().get_object(queryset=queryset)
        check_match_bracket(self, obj)
        return obj
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['bracket'] = self.bracket
        context['editing'] = True
        return context
    
    
    def get_success_url(self):
        return reverse('kata:bracket', args=[self.bracket.id])


@method_decorator(require_POST, name='dispatch')
class KataBracketDeleteMatch(DeleteView):
    template_name = 'kata/katabracket_detail.html'
    model = KataMatch
    
    def get_object(self, queryset=None):
        
        obj = super().get_object(queryset=queryset)
        check_match_bracket(self, obj)
        return obj
    
    
    def delete(self, request, *args, **kwargs):
        
        obj = self.get_object()
        round = obj.round
        p = obj.eventlink
        
        ret = super().delete(request, *args, **kwargs)
        
        if p.is_manual:
            p.delete()
        round.match_callback(None)
        
        return ret
    
    
    def get_success_url(self):
        return reverse('kata:bracket', args=[self.bracket.id])


class KataBracketAddMatch(KataBracketDetails, FormView):
    template_name = 'kata/katabracket_detail.html'
    
    form_class = KataBracketAddPersonForm
    
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['division'] = self.get_object().division
        return kwargs
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.object = self.get_object()
        return super().post(request, *args, **kwargs)
    
    
    def form_valid(self, form):
        
        p = form.cleaned_data['existing_eventlink'] 
        if p is None:
            p = form.instance
            p.save()
        self.get_object().add_person(p)
        
        
        return super().form_valid(form)
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['add_form'] = self.get_form()
        return context
    
    
    def get_success_url(self):
        return reverse('kata:bracket', args=[self.object.id])
#
# class KataBracketEditMatch(generic.detail.SingleObjectMixin, generic.FormView):
#     template_name = 'kata/katabracket_detail.html'
#     form_class = KataMatchForm
#     model = KataBracket
#
#     def get_form_kwargs(self):
#         kwargs = super().get_form_kwargs()
#         kwargs['division'] = self.object
#         return kwargs
#
#     def form_valid(self, form):
#         form.instance.save()
#         return super().form_valid(form)
#
#
#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         return super().post(request, *args, **kwargs)
#
#     def get_success_url(self):
#         return reverse('registration:division-detail', kwargs={'pk': self.object.pk})