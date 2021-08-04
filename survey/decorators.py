import logging
from datetime import date
from functools import wraps

from django.shortcuts import Http404, get_object_or_404

from survey.models import Survey


def valid_survey(func):
    """
    Checks if a survey is valid.
    """

    @wraps(func)
    def survey_check(self, request, *args, **kwargs):
        survey = get_object_or_404(
            Survey.objects.prefetch_related("questions"), id=kwargs["id"])
        return func(self, request, *args, **kwargs, survey=survey)

    return survey_check