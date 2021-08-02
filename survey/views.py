from django.views.generic import TemplateView

from .models import Survey


class IndexView(TemplateView):
    template_name = "survey/list.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        surveys = Survey.objects.all()
        context["surveys"] = surveys
        return context
