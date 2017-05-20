from django.shortcuts import render
from django.views import generic
from django.views.generic.edit import CreateView, UpdateView, DeleteView, ModelFormMixin, FormView
from django.core.urlresolvers import reverse_lazy

from .models import Scoring
from .forms import ScoringForm

# Create your views here.

class KataScoreList(generic.ListView):
    model = Scoring

class KataScoreListWithAdd(CreateView):
    template_name = "KataScore/scoring_list.html"
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
    template_name = "KataScore/scoring_list_update_inline.html"
    form_class = ScoringForm
    
    def get_success_url(self):
        return '/kata_score/list/inline/{}/'.format(self.object.id)
    
class KataScoreListDisplayInline(generic.DetailView):
    model = Scoring
    template_name = "KataScore/scoring_list_display_inline.html"