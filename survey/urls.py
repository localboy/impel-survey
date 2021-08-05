from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import ConfirmView, IndexView, SurveyPerticipated, SurveyInstruction, SurveyDetail, TimeOutView, timeout

urlpatterns = [
    path('', staff_member_required(IndexView.as_view()), name='survey-list'),
    path('api/survey/<id>/timeout/', timeout, name='api-survey-timeout'),
    path('survey/<id>/instructions/', staff_member_required(SurveyInstruction.as_view()), name='survey-instructions'),
    path('survey-participated/', SurveyPerticipated.as_view(), name='survey-participated'),
    path('survey/<id>/', staff_member_required(SurveyDetail.as_view()), name='survey-detail'),
    path('<id>-<step>/', staff_member_required(SurveyDetail.as_view()), name="survey-detail-step"),
    path('survey/<response_id>/confirm/', staff_member_required(ConfirmView.as_view()), name="survey-confirmation"),
    path('survey/<response_id>/timeout/', staff_member_required(TimeOutView.as_view()), name="survey-timeout"),
]