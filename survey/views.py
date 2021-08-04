from django.views.generic import TemplateView, View
from django.shortcuts import redirect, render, reverse

from survey.decorators import survey_available
from .forms import ResponseForm
from .models import Survey


class IndexView(TemplateView):
    template_name = "survey/list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        surveys = Survey.objects.all()
        context["surveys"] = surveys
        return context


class SurveyInstruction(TemplateView):
    template_name = 'survey/instruction.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['survey'] = Survey.objects.get(id=kwargs['id'])
        return context
