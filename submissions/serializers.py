from rest_framework import serializers
from .models import Submission


class SubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Submission
        fields = "__all__"
        read_only_fields = ["student"]






# return feedback with fewer fields
# class FeedbackSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = Submission
#         fields = ["id", "feedback"]
#         read_only_fields = ["id", "feedback"]