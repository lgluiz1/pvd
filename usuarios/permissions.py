from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Apenas administradores."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_admin


class IsGerente(BasePermission):
    """Administradores e gerentes."""
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_gerente


class IsOperador(BasePermission):
    """Qualquer usuário autenticado (incluindo operador)."""
    def has_permission(self, request, view):
        return request.user.is_authenticated
