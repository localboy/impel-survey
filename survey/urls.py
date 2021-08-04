from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import ConfirmView, IndexView, SurveyPerticipated, SurveyInstruction, SurveyDetail

urlpatterns = [
    path('', staff_member_required(IndexView.as_view()), name='survey-list'),
    path('survey/<id>/instructions/', SurveyInstruction.as_view(), name='survey-instructions'),
    path('survey-participated/', SurveyPerticipated.as_view(), name='survey-participated'),    
    path('survey/<id>/', SurveyDetail.as_view(), name='survey-detail'),
    path('<id>-<step>/', SurveyDetail.as_view(), name="survey-detail-step"),
    path('survey/<response_id>/confirm/', ConfirmView.as_view(), name="survey-confirmation"),
]