from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import IndexView, SurveyInstruction

urlpatterns = [
    path('', staff_member_required(IndexView.as_view()), name='survey-list'),
    path('survey/<id>/instructions/', SurveyInstruction.as_view(), name='survey-instructions'),
]