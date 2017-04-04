from rest_framework import permissions
from django_logging import log


class IsAdmin(permissions.BasePermission):

    """
    Custom permission to allow restrict view to members of 'admin' group.
    """

    def has_permission(self, request, view):
        """
        See if user has 'admin' permissions

        :request: HTTP request object
        :view: view to check
        :obj: TODO
        :returns: TODO

        """
        log.debug({"msg": "Checking if %s has admin permission" % request.user})
        if request.user.groups.filter(name='admin').exists():
            return True
        return False


class IsOwnerOrReadOnly(permissions.BasePermission):

    """
    Custom permission to only allow owners of an object to edit it.
    """

    def has_object_permission(self, request, view, obj):
        """
        Read permissions are allowed to any request,
        so we'll always allow GET, HEAD, or OPTIONS requests.

        :request: TODO
        :view: TODO
        :obj: TODO
        :returns: TODO

        """
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to the owner of the object
        return obj.owner == request.user
