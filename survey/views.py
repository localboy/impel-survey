import logging
from django.views.generic import TemplateView, View
from django.shortcuts import redirect, render, reverse, get_object_or_404

from survey.decorators import valid_survey
from .forms import ResponseForm
from .models import Response, Survey

LOGGER = logging.getLogger(__name__)


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


class SurveyDetail(View):
    """
    View for getting user input of a survey
    """

    @valid_survey
    def setup(self, request, *args, **kwargs):
        """
        Setup session and initializing values
        """
        self.survey = kwargs.get("survey")
        self.step = kwargs.get("step", 0)
        self.session_key = 'survey_{}_{}'.format(request.user.id, kwargs['id'])
        if self.session_key not in request.session:
            request.session[self.session_key] = {}

        self.session_data = request.session[self.session_key]

        return super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        template_name = "survey/survey.html"
        form = ResponseForm(
            survey=self.survey,
            user=request.user,
            step=self.step,
            session_data=self.session_data
        )
        context = {
            "response_form": form,
            "survey": self.survey,
            "step": self.step,
        }
        return render(request, template_name, context)

    def post(self, request, *args, **kwargs):
        survey = kwargs.get("survey")
        form = ResponseForm(
            request.POST,
            survey=self.survey,
            user=request.user,
            step=self.step,
            session_data=self.session_data
        )
        context = {"response_form": form, "survey": survey}
        if form.is_valid():
            return self.treat_valid_form(form, kwargs, request, self.survey)
        return self.handle_invalid_form(context, request)

    @staticmethod
    def handle_invalid_form(context, request):
        template_name = "survey/list.html"
        return render(request, template_name, context)

    def treat_valid_form(self, form, kwargs, request, survey):
        session_key = self.session_key

        # Saving data in session
        for key, value in list(form.cleaned_data.items()):
            request.session[session_key][key] = value
            request.session.modified = True
        next_url = form.next_step_url()
        response = None

        # when it's the last step
        if not form.has_next_step():
            save_form = ResponseForm(
                request.session[session_key],
                survey=survey,
                user=request.user,
                session_data=self.session_data
            )
            if save_form.is_valid():
                response = save_form.save()
            else:
                LOGGER.warning("A step of the multipage form failed",
                "but should have been discovered before.")

        # if there is a next step
        if next_url is not None:
            return redirect(next_url)
        del request.session[session_key]
        if response is None:
            return redirect(reverse("survey-list"))
        next_ = request.session.get("next", None)
        if next_ is not None:
            if "next" in request.session:
                del request.session["next"]
            return redirect(next_)
        return redirect("survey-confirmation", response_id=response.id)


class ConfirmView(TemplateView):
    template_name = 'survey/confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response'] = get_object_or_404(Response, id=kwargs['response_id'])
        return context
