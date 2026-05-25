from django.urls import path
from .views import (
    SubmissionCreateView,
    SubmissionListView,
    SubmissionFeedbackView
)

urlpatterns = [
    path("", SubmissionListView.as_view(), name="submission-list"),
    path("create/", SubmissionCreateView.as_view(), name="submission-create"),
    path("<int:pk>/feedback/", SubmissionFeedbackView.as_view(), name="submission-feedback"),
]