from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import IndexView, SurveyInstruction, SurveyDetail

urlpatterns = [
    path('', staff_member_required(IndexView.as_view()), name='survey-list'),
    path('survey/<id>/instructions/', SurveyInstruction.as_view(), name='survey-instructions'),
    path('survey/<id>/', SurveyDetail.as_view(), name='survey-detail'),
    path('<id>-<step>/', SurveyDetail.as_view(), name="survey-detail-step"),
]