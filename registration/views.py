from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied

from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView, ModelFormMixin

from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from .models import Person, Rank, EventLink, Division
from .forms import PersonForm, ManualEventLinkForm, PersonFilterForm, PersonCheckinForm, PersonPaidForm, TeamAssignForm

# Create your views here.

class IndexView(PermissionRequiredMixin, generic.ListView, generic.edit.FormMixin):
    """Main view for displaying the registered competetors.

    Related to :class:`.IndexViewTable` and :class:`.IndexViewTableRow` which are used to redraw parts of this view
    dynamically. Views :class:`PersonPaid` and :class:`PersonCheckin` are called by clicking buttons in this view.

    """

    model = Person
    form_class = PersonFilterForm
    permission_required = 'accounts.edit'
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.form = None
    
    
    def get_form_kwargs(self):
        
        kwargs = {
            'initial': self.get_initial(),
            'prefix': self.get_prefix(),
        }
        if self.request.method in ('POST', 'PUT'):
            kwargs.update({
                'data': self.request.POST,
            })
        elif self.request.method in ('GET', ):
            kwargs.update({
                'data': self.request.GET,
            })
        return kwargs
    
    
    def get(self, request, *args, **kwargs):
        self.form = self.get_form()
        return super().get(request, *args, **kwargs)
    
    
    def get_queryset(self):
        
        qs = self.model.objects.all()
        
        if self.form.is_valid():
            qs = self.form.filter(qs)
        
        return qs


class IndexViewTable(IndexView):
    template_name = "registration/person_list_table.html"


class IndexViewTableRow(PermissionRequiredMixin, generic.DetailView):
    model = Person
    template_name = "registration/person_list_table_row.html"
    permission_required = 'account.edit'

class DetailView(generic.DetailView):
    model = Person


class PersonCreate(CreateView):
    model = Person
    form_class = PersonForm
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        for event in form.cleaned_data['events']:
            link = EventLink(event=event, person=self.object)
            link.save()
        return HttpResponseRedirect(self.get_success_url())
    

class PersonUpdate(UpdateView):
    model = Person
    form_class = PersonForm
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        if 'events' in form.changed_data:
            # Clear links for removed events
            link_set = self.object.eventlink_set.all()
            for link in link_set:
                if link.event not in form.cleaned_data['events']:
                    link.delete()
            # Create links for added events
            for event in form.cleaned_data['events']:
                if link_set.filter(event=event).count() == 0:
                    link = EventLink(event=event, person=self.object)
                    link.save()
        return HttpResponseRedirect(self.get_success_url())


class PersonDelete(DeleteView):
    model = Person
    success_url = reverse_lazy('registration:index')


class PersonCheckin(UpdateView):
    model = Person
    form_class = PersonCheckinForm
    inline = False
    
    def dispatch(self, request, *args, **kwargs):
        if "inline" in request.GET:
            self.inline = True
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        if self.inline:
            return reverse('registration:index-table-row', args=[self.object.pk,])
        else:
            return reverse('registration:index')


class PersonPaid(UpdateView):
    model = Person
    form_class = PersonPaidForm
    inline = False
    
    def dispatch(self, request, *args, **kwargs):
        if "inline" in request.GET:
            self.inline = True
        return super().dispatch(request, *args, **kwargs)
    
    def get_success_url(self):
        if self.inline:
            return reverse('registration:index-table-row', args=[self.object.pk,])
        else:
            return reverse('registration:index')


class DivisionList(generic.ListView):
    model = Division
    orderby = ('event', 'start_age', 'start_rank__order',)
    
    def get_context_data(self, **kwargs):
        context = super(DivisionList, self).get_context_data(**kwargs)
        context['no_division_eventlist'] = EventLink.no_division_eventlinks()
        return context


def add_division_info_context_data(view, context, **kwargs):
    context['locked'] = view.object.get_format() is not None
    context['confirmed_eventlinks'] = view.object.get_confirmed_eventlinks()
    context['noshow_eventlinks'] = view.object.get_noshow_eventlinks()
    if 'add_form' not in context:
        context['add_form'] = ManualEventLinkForm()
    if view.object.event.is_team:
        context['team_assign_form'] = TeamAssignForm(view.object)
    
    return context


class DivisionInfo(generic.DetailView):
    model = Division
    
    def get_template_names(self):
        if self.object.event.is_team:
            return ['registration/division_team_detail.html']
        else:
            return ['registration/division_detail.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = add_division_info_context_data(self, context)
        return context


@method_decorator(require_POST, name='dispatch')
class DivisionAddManualPerson(generic.detail.SingleObjectMixin, generic.FormView):
    form_class = ManualEventLinkForm
    model = Division
    
    def get_template_names(self):
        if self.object.event.is_team:
            return ['registration/division_team_detail.html']
        else:
            return ['registration/division_detail.html']
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context = add_division_info_context_data(self, context)
        return context
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['division'] = self.object
        return kwargs
    
    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)
    
    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(add_form=form))
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        return self.object.get_absolute_url()


@method_decorator(require_POST, name='dispatch')
class TeamAssignView(DivisionInfo, FormView):
    form_class = TeamAssignForm
    
    
    def get_context_data(self, form=None):
        context = super().get_context_data(**kwargs)
        context = add_division_info_context_data(self, context)
        return context
    
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['division'] = self.get_object()
        return kwargs
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
    
    
    def form_valid(self, form):
        
        el1 = form.cleaned_data['src']
        old_team = el1.team
        
        el2 = form.cleaned_data['tgt']
        if el2 is None:
            el2 = EventLink(division=self.object, event=self.object.event, is_team=True)
            el2.save()
        elif not el2.is_team:
            team = EventLink(division=self.object, event=self.object.event, is_team=True)
            team.save()
            el2.team = team
            el2.save()
            el2 = team
        
        el1.team = el2
        el1.save()
        
        if old_team is not None and old_team.eventlink_set.count() == 0:
            old_team.delete()
        
        return super().form_valid(form)
    
    
    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(team_assign_form=form))
    
    
    def get_success_url(self):
        return self.object.get_absolute_url()


@method_decorator(require_POST, name='dispatch')
class DivisionDeleteManaualPerson(generic.DeleteView):
    template_name = 'registration/division_detail.html' # Value doesn't matter since HTTP Get is forbidden
    model = EventLink
    
    def get_object(self):
      obj = super().get_object()
      if obj.is_manual:
        return obj
      raise PermissionDenied
    
    def get_success_url(self):
        return self.object.division.get_absolute_url()
    
    def delete(self, request, *args, **kwargs):
        
        old_team = self.get_object().team
        ret = super().delete(request, *args, **kwargs)
        if old_team is not None and old_team.eventlink_set.count() == 0:
            old_team.delete()
        return ret


@method_decorator(require_POST, name='dispatch')
class DivisionBuild(generic.detail.SingleObjectMixin, generic.View):
    model = Division
    
    def post(self, request, *args, **kwargs):
        
        div = self.get_object()
        fmt = div.get_format()
        if fmt is None:
            fmt = div.build_format()
        
        return HttpResponseRedirect(fmt.get_absolute_url())
        