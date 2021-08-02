from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .views import IndexView

urlpatterns = [
    path('', staff_member_required(IndexView.as_view()), name='survey-list'),
]