from rest_framework.response import Response
from rest_framework.decorators import api_view


@api_view(['GET'])
def welcome(request):
    return Response({
        "message": "Welcome to the Classroom Feedback API",
        "version": "1.0"
    })
