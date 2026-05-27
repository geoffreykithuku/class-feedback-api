from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Submission
from .serializers import SubmissionSerializer

from accounts.permissions import IsStudent, IsInstructor, IsObserver
from accounts.models import ObserverStudentLink
from assignments.models import Assignment

class SubmissionCreateView(generics.CreateAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated, IsStudent]

    def perform_create(self, serializer):

        # We NEVER accept student identity from the frontend.
        # Even if a malicious user sends another student's ID,
        # we override it using request.user (trusted identity).

        serializer.save(student=self.request.user)

class SubmissionListView(generics.ListAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        # Instructor sees submissions for THEIR assignments only
        if user.role == "instructor":
            return Submission.objects.filter(
                assignment__instructor=user
            )

        # Student sees ONLY their own submissions
        if user.role == "student":
            return Submission.objects.filter(student=user)

        # Observer sees ONLY linked student's submissions
        if user.role == "observer":
            linked = ObserverStudentLink.objects.get(observer=user)
            return Submission.objects.filter(student=linked.student)

        return Submission.objects.none()
    


class SubmissionFeedbackView(generics.RetrieveUpdateAPIView):
    serializer_class = SubmissionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user

        # Instructor can only access submissions for their assignments
        if user.role == "instructor":
            return Submission.objects.filter(
                assignment__instructor=user
            )
        
        # Student can view feedback for their own submissions
        if user.role == "student":
            return Submission.objects.filter(student=user)
        
        
        # Observer can view feedback for linked student's submissions
        if user.role == "observer":
            linked = ObserverStudentLink.objects.get(observer=user)
            return Submission.objects.filter(student=linked.student)
        return Submission.objects.none()
    