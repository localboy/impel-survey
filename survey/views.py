import logging
from datetime import datetime, timedelta
from django.http.response import JsonResponse
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
        surveys = Survey.objects.exclude(responses__user=self.request.user)    
        context["surveys"] = surveys
        return context


class SurveyInstruction(View):
    """
    View for instructions
    """

    @valid_survey
    def get(self, request, *args, **kwargs):
        survey_status = kwargs['survey_status']
        # Checking if already participated
        if survey_status and survey_status in ['participated', 'timeout']:
            return redirect(reverse("survey-participated"))

        session_key = kwargs['session_key']
        survey = kwargs['survey']
        if session_key in request.session:
            return redirect(survey.get_absolute_url())
        template_name = 'survey/instruction.html'
        context = {}
        context['survey'] = survey
        return render(request, template_name, context)


class SurveyDetail(View):
    """
    View for getting user input of a survey
    """

    @valid_survey
    def setup(self, request, *args, **kwargs):
        """
        Setup session and initializing values
        """
        self.survey_status = kwargs['survey_status']
        self.survey = kwargs.get("survey")
        self.step = kwargs.get("step", 0)
        self.session_key = 'survey_{}_{}'.format(request.user.id, kwargs['id'])
        if self.session_key not in request.session:
            request.session[self.session_key] = {}
            request.session[self.session_key]['end_date'] = datetime.timestamp(datetime.now())
            request.session[self.session_key]['end_date'] = datetime.timestamp(
                datetime.now() + timedelta(minutes=self.survey.duration))

        remaining_time = request.session[self.session_key]['end_date'] - datetime.timestamp(datetime.now())
        request.session[self.session_key]['remaining'] = remaining_time if remaining_time>=0 else 0
        self.session_data = request.session[self.session_key]

        return super().setup(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):

        # Checking if already participated
        if self.survey_status and self.survey_status in ['participated', 'timeout']:
            return redirect(reverse("survey-participated"))

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
            "time_remaining": int(self.session_data['remaining']),
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
        request_step = request.POST['step_type']
        if request_step == 'Prev!':
            # if there is previous step
            prev_url = form.prev_step_url()
            if prev_url is not None:
                return redirect(prev_url)
            prev_ = request.session.get("prev", None)
            if prev_ is  not None:
                if "prev" in request.session:
                    del request.session["prev"]
                return redirect(prev_)
        else:
            # if there is a next step
            next_url = form.next_step_url()
            if next_url is not None:
                return redirect(next_url)
            next_ = request.session.get("next", None)
            if next_ is not None:
                if "next" in request.session:
                    del request.session["next"]
                return redirect(next_)        

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
        del request.session[session_key]
        if response is None:
            return redirect(reverse("survey-list"))
        return redirect("survey-confirmation", response_id=response.id)


class ConfirmView(TemplateView):
    template_name = 'survey/confirmation.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response'] = get_object_or_404(Response, id=kwargs['response_id'])
        return context


class SurveyPerticipated(TemplateView):

    template_name = 'survey/participated.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class TimeOutView(TemplateView):
    """
    View to show timeout message.
    """
    template_name = 'survey/timeout.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['response'] = get_object_or_404(Response, id=kwargs['response_id'])
        context["msg"] = "Your time is out. Thanks for perticipating in the survey"
        return context


def timeout(request, id: int):
    """
    API endpoint for saving user input from session of a survey when 
    the survey time is out.
    """

    session_key = 'survey_{}_{}'.format(request.user.id, id)
    survey = get_object_or_404(Survey, id=id)
    if session_key in request.session:
        session_data = request.session[session_key]
        save_form = ResponseForm(
            request.session[session_key],
            survey=survey,
            user=request.user,
            session_data=session_data
        )
        if save_form.is_valid():
            response = save_form.save()
            del request.session[session_key]
            return JsonResponse(
                {"status": "success", "response_id": response.id},
                status=200)
        else:
            return JsonResponse({"status": "fail"}, status=400)
