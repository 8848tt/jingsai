from rest_framework import permissions

from apps.accounts.models import User


def _is_admin(user) -> bool:
    return user.is_authenticated and getattr(user, "role", None) == User.Role.ADMIN


def _is_expert(user) -> bool:
    return user.is_authenticated and getattr(user, "role", None) == User.Role.EXPERT


def _is_student(user) -> bool:
    return user.is_authenticated and getattr(user, "role", None) == User.Role.STUDENT


class IsAdminUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return _is_admin(request.user)


class IsStudentUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return _is_student(request.user)


class IsExpertUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return _is_expert(request.user)


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS


class IsTeamLeader(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.leader_id == request.user.id


class IsTeamMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        from .models import TeamMembership

        if obj.leader_id == request.user.id:
            return True
        return obj.memberships.filter(
            student=request.user, status=TeamMembership.Status.APPROVED
        ).exists()
