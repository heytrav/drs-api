import logging
from django.contrib.auth.models import User
from domain_api.permissions import IsOwnerOrReadOnly
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, generics, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.reverse import reverse
from domain_api.models import (
    PersonalDetail,
    ContactType,
    TopLevelDomain,
    TopLevelDomainProvider,
    DomainProvider,
    RegistrantHandle,
    ContactHandle,
    Domain,
    RegisteredDomain,
    DomainRegistrant,
    DomainHandles,
    TopLevelDomainProvider
)
from domain_api.serializers import (
    UserSerializer,
    PersonalDetailSerializer,
    ContactTypeSerializer,
    ContactHandleSerializer,
    TopLevelDomainSerializer,
    TopLevelDomainProviderSerializer,
    DomainProviderSerializer,
    RegistrantHandleSerializer,
    DomainSerializer,
    RegisteredDomainSerializer,
    CheckDomainResponseSerializer,
)


logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def check_domain(request, domain, format=None):
    """
    Query EPP with a checkDomain request.
    :returns: JSON response indicating whether domain is available.

    """
    logger.debug("Received request for domain: ", domain)
    response_data = {"result": [{"domain": domain, "available": True}]}
    serializer = CheckDomainResponseSerializer(data=response_data)
    if serializer.is_valid():
        return Response(serializer.data)


class UserViewSet(viewsets.ReadOnlyModelViewSet):

    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class PersonalDetailViewSet(viewsets.ModelViewSet):

    """Docstring for PersonalDetailViewSet. """
    queryset = PersonalDetail.objects.all()
    serializer_class = PersonalDetailSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class ContactTypeViewSet(viewsets.ModelViewSet):

    """
    Contact type view
    """
    queryset = ContactType.objects.all()
    serializer_class = ContactTypeSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomain.objects.all()
    serializer_class = TopLevelDomainSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DomainProviderViewSet(viewsets.ModelViewSet):

    queryset = DomainProvider.objects.all()
    serializer_class = DomainProviderSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RegistrantHandleViewSet(viewsets.ModelViewSet):

    queryset = RegistrantHandle.objects.all()
    serializer_class = RegistrantHandleSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ContactHandleViewSet(viewsets.ModelViewSet):

    queryset = ContactHandle.objects.all()
    serializer_class = ContactHandleSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RegistrantHandleViewSet(viewsets.ModelViewSet):

    queryset = RegistrantHandle.objects.all()
    serializer_class = RegistrantHandleSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ContactHandleViewSet(viewsets.ModelViewSet):

    queryset = ContactHandle.objects.all()
    serializer_class = ContactHandleSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DomainViewSet(viewsets.ModelViewSet):

    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RegisteredDomainViewSet(viewsets.ModelViewSet):

    queryset = RegisteredDomain.objects.all()
    serializer_class = RegisteredDomainSerializer
    permission_classes = (permissions.IsAdminUser,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
