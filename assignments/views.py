from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from .models import Assignment
from .serializers import AssignmentSerializer

from accounts.permissions import IsInstructor

class AssignmentCreateView(generics.CreateAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated, IsInstructor]

    def perform_create(self, serializer):

        # Never trust the frontend to tell us who the instructor is.
        # A malicious user could send another instructor's ID.
        # We always derive identity from request.user because
        # request.user comes from validated JWT authentication.
        
        serializer.save(instructor=self.request.user)


class AssignmentListView(generics.ListAPIView):
    serializer_class = AssignmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user

        if user.role == "instructor":
            return Assignment.objects.filter(instructor=user)

        return Assignment.objects.all()