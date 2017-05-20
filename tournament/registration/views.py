from django.http import HttpResponse
from django.shortcuts import render
from django.core.urlresolvers import reverse_lazy

from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin

from .models import Person, Rank, EventLink, Division
from .forms import PersonForm

# Create your views here.
def index(request):
    return HttpResponse("Hello, world. You're at the index.")


class IndexView(generic.ListView):
    model = Person


class DetailView(generic.DetailView):
    model = Person


class PersonCreate(CreateView):
    model = Person
    form_class = PersonForm
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        for event in form.cleaned_data['events2']:
            link = EventLink()
            link.person = self.object
            link.event = event
            link.save()
        return super(ModelFormMixin, self).form_valid(form)
    

class PersonUpdate(UpdateView):
    model = Person
    form_class = PersonForm
    
    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.save()
        if 'events' in form.changed_data:
            self.object.events.clear() # Remove existing links and recreate
            for event in form.cleaned_data['events']:
                link = EventLink()
                link.person = self.object
                link.event = event
                link.save()
        return super(ModelFormMixin, self).form_valid(form)


class PersonDelete(DeleteView):
    model = Person
    success_url = reverse_lazy('index')
    
    
class DivisionList(generic.ListView):
    model = Division
    orderby = ('event', 'start_age', 'start_rank__order',)
    
    def get_context_data(self, **kwargs):
        context = super(DivisionList, self).get_context_data(**kwargs)
        context['no_division_eventlist'] = EventLink.objects.filter(division=None)
        return context