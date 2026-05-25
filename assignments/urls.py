from django.urls import path
from .views import AssignmentCreateView, AssignmentListView

urlpatterns = [
    path("", AssignmentListView.as_view(), name="assignment-list"),
    path("create/", AssignmentCreateView.as_view(), name="assignment-create"),
]