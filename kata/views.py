from django.contrib.auth.mixins import PermissionRequiredMixin
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.urls import reverse_lazy, reverse
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from registration.models import EventLink

from .models import KataBracket, KataRound, KataMatch
from .forms import KataMatchForm, KataBracketAddPersonForm, KataBracketAddTeamForm

# Create your views here.

class KataBracketDetails(PermissionRequiredMixin, generic.DetailView):
    model = KataBracket
    context_object_name = "bracket"
    permission_required = 'accounts.view'
    
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['editing'] = False
        
        if self.object.division.event.is_team:
            context['add_form'] = KataBracketAddTeamForm(self.object.division)
            context['add_form_url'] = reverse('kata:bracket-team-match-add', args=[self.object.id])
        else:
            context['add_form'] = KataBracketAddPersonForm(self.object.division)
            context['add_form_url'] = reverse('kata:bracket-match-add', args=[self.object.id])
        
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
    

class KataBracketEditMatch(PermissionRequiredMixin, UpdateView):
    template_name = 'kata/katabracket_detail.html'
    model = KataMatch
    form_class = KataMatchForm
    permission_required = 'accounts.edit'
    
    
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
        return reverse('kata:bracket', args=[self.bracket.id]) + "?highlight={}".format(self.object.id)


@method_decorator(require_POST, name='dispatch')
class KataBracketDeleteMatch(PermissionRequiredMixin, DeleteView):
    template_name = 'kata/katabracket_detail.html'
    model = KataMatch
    permission_required = 'accounts.edit'
    
    def get_object(self, queryset=None):
        
        obj = super().get_object(queryset=queryset)
        check_match_bracket(self, obj)
        return obj
    
    
    def delete(self, request, *args, **kwargs):
        
        obj = self.get_object()
        round = obj.round
        p = obj.eventlink
        
        ret = super().delete(request, *args, **kwargs)
        
        # Delete manual event links that are part of the team. 
        
        if p.is_manual or p.is_team:
            p.delete()
        round.match_callback(None)
        
        return ret
    
    
    def get_success_url(self):
        return reverse('kata:bracket', args=[self.bracket.id])


class KataBracketAddMatch(KataBracketDetails, FormView):
    template_name = 'kata/katabracket_detail.html'
    form_class = KataBracketAddPersonForm
    permission_required = 'accounts.edit'
    
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['division'] = self.get_object().division
        return kwargs
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.object = self.get_object()
        return super().post(request, *args, **kwargs)
    
    
    def form_valid(self, form, skip=False):
        
        if not skip:
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


class KataBracketAddTeamMatch(KataBracketAddMatch):
    form_class = KataBracketAddTeamForm
    permission_required = 'accounts.edit'
    
    
    def form_valid(self, form):
        
        p = form.cleaned_data['existing_eventlink'] 
        if p is None:
            p = form.instance
        
        team = form.cleaned_data['team']
        new_team = team is None
        if new_team:
            team = EventLink(event=p.event, division=p.division, is_team=True)
            team.save()
        
        p.team = team
        p.save()
        
        if new_team:
            self.get_object().add_person(team)
        
        return super().form_valid(form, skip=True)

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