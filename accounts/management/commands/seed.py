from django.core.management.base import BaseCommand
from accounts.models import User, ObserverStudentLink
from assignments.models import Assignment
from submissions.models import Submission


class Command(BaseCommand):
    help = "Seed demo data for classroom system"

    def handle(self, *args, **kwargs):

        # Clear old data
        Submission.objects.all().delete()
        Assignment.objects.all().delete()
        ObserverStudentLink.objects.all().delete()
        User.objects.all().delete()

        instructor = User.objects.create_user(
            email="instructor@demo.dev",
            password="Demo@1234",
            role="instructor"
        )

        student = User.objects.create_user(
            email="student@demo.dev",
            password="Demo@1234",
            role="student"
        )

        observer = User.objects.create_user(
            email="observer@demo.dev",
            password="Demo@1234",
            role="observer"
        )

        ObserverStudentLink.objects.create(
            observer=observer,
            student=student
        )

        assignment1 = Assignment.objects.create(
            title="Django Auth Basics",
            description="Implement JWT authentication",
            instructor=instructor
        )

        assignment2 = Assignment.objects.create(
            title="RBAC System",
            description="Build role-based access control",
            instructor=instructor
        )

        Submission.objects.create(
            assignment=assignment1,
            student=student,
            content="My JWT implementation"
        )

        Submission.objects.create(
            assignment=assignment2,
            student=student,
            content="RBAC implementation"
        )

        self.stdout.write(self.style.SUCCESS("Demo data created successfully"))