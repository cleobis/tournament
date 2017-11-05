from django.http import HttpResponse
from django.http.response import HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy, reverse
from django.core.exceptions import PermissionDenied

from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin

from django.utils.decorators import method_decorator
from django.views.decorators.http import require_POST

from .models import Person, Rank, EventLink, Division
from .forms import PersonForm, ManualEventLinkForm, PersonFilterForm

# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the index.")


class IndexView(generic.ListView, generic.edit.FormMixin):
    model = Person
    form_class = PersonFilterForm
    
    
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
            self.object.events.clear() # Remove existing links and recreate
            for event in form.cleaned_data['events']:
                link = EventLink(event=event, person=self.object)
                link.save()
        return HttpResponseRedirect(self.get_success_url())


class PersonDelete(DeleteView):
    model = Person
    success_url = reverse_lazy('registration:index')
    
    
class DivisionList(generic.ListView):
    model = Division
    orderby = ('event', 'start_age', 'start_rank__order',)
    
    def get_context_data(self, **kwargs):
        context = super(DivisionList, self).get_context_data(**kwargs)
        context['no_division_eventlist'] = EventLink.objects.filter(division=None)
        return context


class DivisionInfoDispatch(generic.View):
    
    # See https://docs.djangoproject.com/en/1.8/topics/class-based-views/mixins/#using-formmixin-with-detailview
    
    def get(self, request, *args, **kwargs):
        view = DivisionInfo.as_view()
        return view(request, *args, **kwargs)
    
    
    def post(self, request, *args, **kwargs):
        
        view = DivisionAddManualPerson.as_view()
        return view(request, *args, **kwargs)


class DivisionInfo(generic.DetailView):
    model = Division
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        context['form'] = ManualEventLinkForm()
        
        return context


class DivisionAddManualPerson(generic.detail.SingleObjectMixin, generic.FormView):
    template_name = 'registration/division_detail.html'
    form_class = ManualEventLinkForm
    model = Division
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['division'] = self.object
        return kwargs
    
    def form_valid(self, form):
        form.instance.save()
        return super().form_valid(form)
    
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        return super().post(request, *args, **kwargs)
    
    def get_success_url(self):
        return reverse('registration:division-detail', kwargs={'pk': self.object.pk})


class DivisionDeleteManaualPerson(generic.DeleteView):
    template_name = 'registration/division_detail.html'
    model = EventLink
    
    def get_object(self):
      obj = super().get_object()
      if obj.is_manual:
        return obj
      raise PermissionDenied
    
    def get_success_url(self):
        return reverse('registration:division-detail', kwargs={'pk': self.object.division.pk})
    
    def get(self, *args, **kwargs):
        return HttpResponseForbidden()


@method_decorator(require_POST, name='dispatch')
class DivisionBuild(generic.detail.SingleObjectMixin, generic.View):
    model = Division
    
    def post(self, request, *args, **kwargs):
        
        div = self.get_object()
        fmt = div.get_format()
        if fmt is None:
            fmt = div.build_format()
        
        return HttpResponseRedirect(fmt.get_absolute_url())
        