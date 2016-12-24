from django.contrib.auth.models import User
from domain_api.permissions import IsOwnerOrReadOnly
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, generics, permissions, viewsets
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse
from domain_api.models import (
    Identity,
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
    IdentitySerializer,
    UserSerializer,
    PersonalDetailSerializer,
    ContactTypeSerializer,
    ContactHandleSerializer,
    TopLevelDomainSerializer,
    TopLevelDomainProviderSerializer,
    DomainProviderSerializer,
    RegistrantHandleSerializer,
    DomainSerializer,
    RegisteredDomainSerializer
)


class IdentityViewSet(viewsets.ModelViewSet):

    """
    This viewset automatically provides `list`, `create`, `retrieve`,
    `update` and `destroy` actions.
    """
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


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
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomain.objects.all()
    serializer_class = TopLevelDomainSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DomainProviderViewSet(viewsets.ModelViewSet):

    queryset = DomainProvider.objects.all()
    serializer_class = DomainProviderSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RegistrantHandleViewSet(viewsets.ModelViewSet):

    queryset = RegistrantHandle.objects.all()
    serializer_class = RegistrantHandleSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ContactHandleViewSet(viewsets.ModelViewSet):

    queryset = ContactHandle.objects.all()
    serializer_class = ContactHandleSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RegistrantHandleViewSet(viewsets.ModelViewSet):

    queryset = RegistrantHandle.objects.all()
    serializer_class = RegistrantHandleSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ContactHandleViewSet(viewsets.ModelViewSet):

    queryset = ContactHandle.objects.all()
    serializer_class = ContactHandleSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DomainViewSet(viewsets.ModelViewSet):

    queryset = Domain.objects.all()
    serializer_class = DomainSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RegisteredDomainViewSet(viewsets.ModelViewSet):

    queryset = RegisteredDomain.objects.all()
    serializer_class = RegisteredDomainSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
