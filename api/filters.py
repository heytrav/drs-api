from rest_framework import filters


class IsOwnerFilterBackend(filters.BaseFilterBackend):

    """Docstring for IsOwnerFilterBackend. """


    def filter_queryset(self, request, queryset, view):
        """
        Filter a contact handle on a specific owner.

        :request: TODO
        :queryset: TODO
        :view: TODO
        :returns: TODO

        """
        return queryset.filter(owner=request.user)


class IsPersonFilterBackend(filters.BaseFilterBackend):

    """
    Filter querysets on a specific person.
    """

    def filter_queryset(self, request, queryset, view):
        """
        Check if the person in this queryset belongs to the specific owner.

        :request: Request object
        :queryset: Any queryset with a relation to a person
        :view: Any view
        :returns: queryset filtered on the logged in user

        """
        if request.user.is_staff:
            return queryset
        return queryset.filter(person__owner=request.user)
