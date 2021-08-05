import logging
import pytz
from datetime import datetime
from functools import wraps

utc=pytz.UTC

from django.shortcuts import Http404, get_object_or_404, redirect, reverse

from survey.models import Survey


def valid_survey(func):
    """
    Checks if a survey is valid.
    """

    @wraps(func)
    def survey_check(self, request, *args, **kwargs):
        session_key = 'survey_{}_{}'.format(request.user.id, kwargs['id'])
        survey_status = ''
        survey = get_object_or_404(
            Survey.objects.prefetch_related("questions", "responses"), id=kwargs["id"])
        
        if survey.expire_date< utc.localize(datetime.now()):
            msg = "Survey already expired at: '%s'."
            raise Http404

        # checking if there any existing response
        if survey.responses.filter(user=request.user).count() > 0:
            survey_status = 'participated'

        # Once user start the survey, whether he can submit or not,
        # he will not able to participate again.
        if session_key in request.session:
            session_data = request.session[session_key]
            # If survey time is up
            if session_data['remaining'] == 0:
                survey_status = 'timeout'
        return func(self, request, *args, **kwargs, survey=survey, session_key=session_key,\
                    survey_status=survey_status)

    return survey_check
