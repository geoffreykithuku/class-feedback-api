from rest_framework.permissions import BasePermission

class IsInstructor(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "instructor"
    
class IsStudent(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "student"


class IsObserver(BasePermission):
    def has_permission(self, request, view):
        return request.user.role == "observer"

