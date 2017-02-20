from __future__ import absolute_import, unicode_literals
from celery import chain
from django_logging import log, ErrorLogObject
from django.shortcuts import get_object_or_404
# Remove this
from django.contrib.auth.models import User
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from domain_api.models import (
    Domain,
    PersonalDetail,
    ContactType,
    TopLevelDomain,
    DomainProvider,
    RegistrantHandle,
    ContactHandle,
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
    DomainRegistrantSerializer,
    DomainHandlesSerializer,
    InfoDomainSerializer,
)
from domain_api.filters import (
    IsPersonFilterBackend
)
from .epp.queries import Domain as DomainQuery
from .exceptions import (
    EppError,
)
from domain_api.entity_management.contacts import ContactHandleFactory
from domain_api.utilities.domain import parse_domain
from .workflows import workflow_factory


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def check_domain(request, registry, domain, format=None):
    """
    Query EPP with a checkDomain request.
    :returns: JSON response indicating whether domain is available.
    """
    try:
        query = DomainQuery()
        availability = query.check_domain(registry, domain)
        serializer = CheckDomainResponseSerializer(data=availability)
        if serializer.is_valid():
            return Response(serializer.data)
    except EppError as epp_e:
        log.error(ErrorLogObject(request, epp_e))
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except KeyError as ke:
        log.error(ErrorLogObject(request, ke))
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def info_domain(request, registry, domain, format=None):
    """
    Query EPP with a infoDomain request.
    :returns: JSON response with details about a domain

    """
    try:
        query = DomainQuery()
        info = query.info(registry, domain, is_staff=request.user.is_staff)
        serializer = InfoDomainSerializer(data=info)
        log.info(info)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)
    except EppError as epp_e:
        log.error(ErrorLogObject(request, epp_e))
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        log.error(ErrorLogObject(request, e))
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes((permissions.IsAdminUser,))
def registry_contact(request, registry, contact_type="contact"):
    """
    Create or view contacts for a particular registry.

    :registry: Registry to add this contact for
    :returns: A contact object
    """
    provider = get_object_or_404(DomainProvider.objects.all(), slug=registry)

    data = request.data
    log.debug(data)
    person = None
    queryset = PersonalDetail.objects.all()
    if "person" in data:
        person = get_object_or_404(queryset, pk=data["person"])
    else:
        serializer = PersonalDetailSerializer(data=data)
        if serializer.is_valid():
            person = serializer.save(owner=request.user)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        contact_factory = ContactHandleFactory(provider,
                                               contact_type,
                                               context={"request": request})
        serializer = contact_factory.create_registry_contact(person)
        return Response(serializer.data)
    except EppError as epp_e:
        log.error(ErrorLogObject(request, epp_e))
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        log.error(ErrorLogObject(request, e))
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def register_domain(request):
    """
    Register a domain name.

    :request: Request object with JSON payload
    :returns: Response from registry
    """
    data = request.data
    parsed_domain = parse_domain(data["domain"])
    try:
        # See if this TLD is provided by one of our registries.
        tld_provider = TopLevelDomainProvider.objects.get(
            zone=parsed_domain["zone"]
        )
        registry = tld_provider.provider.slug
        workflow_manager = workflow_factory(registry)()

        log.debug({"msg": "About to call workflow_manager.create_domain"})
        workflow = workflow_manager.create_domain(data)
        # run chained workflow and register the domain
        response = chain(workflow)().get()
        return Response(response)
    except KeyError as e:
        log.error(ErrorLogObject(request, e))
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except TopLevelDomainProvider.DoesNotExist:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        log.error(ErrorLogObject(request, e))
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class PersonalDetailViewSet(viewsets.ModelViewSet):

    serializer_class = PersonalDetailSerializer
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """
        Override to make sure that this only returns personal details that belong to logged in user.
        :returns: Filtered set of personal detail objects.

        """
        user = self.request.user
        if user.is_staff:
            return PersonalDetail.objects.all()
        return PersonalDetail.objects.filter(owner=user)


class UserViewSet(viewsets.ReadOnlyModelViewSet):

    """
    This viewset automatically provides `list` and `detail` actions.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.IsAdminUser,)


class ContactTypeViewSet(viewsets.ModelViewSet):

    """
    Contact type view
    """
    queryset = ContactType.objects.all()
    serializer_class = ContactTypeSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


class TopLevelDomainViewSet(viewsets.ModelViewSet):
    """
    Set of top level domains.
    """

    queryset = TopLevelDomain.objects.all()
    serializer_class = TopLevelDomainSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


class DomainProviderViewSet(viewsets.ModelViewSet):
    """
    Set of tld providers.
    """

    queryset = DomainProvider.objects.all()
    serializer_class = DomainProviderSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


class ContactHandleViewSet(viewsets.ModelViewSet):
    """
    Contact handles.
    """

    serializer_class = ContactHandleSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,
                          permissions.IsAuthenticated)
    queryset = ContactHandle.objects.all()
    filter_backends = (IsPersonFilterBackend,)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.IsAdminUser,)


class RegistrantHandleViewSet(viewsets.ModelViewSet):

    serializer_class = RegistrantHandleSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Override to make sure that this only returns personal details that
        belong to logged in user.
        :returns: Filtered set of personal detail objects.

        """
        user = self.request.user
        if user.is_staff:
            return RegistrantHandle.objects.all()
        return RegistrantHandle.objects.filter(person__owner=user)


class DomainViewSet(viewsets.ModelViewSet):

    serializer_class = DomainSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Domain.objects.all()


class RegisteredDomainViewSet(viewsets.ModelViewSet):

    serializer_class = RegisteredDomainSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)
    queryset = RegisteredDomain.objects.all()



class DomainRegistrantViewSet(viewsets.ModelViewSet):

    serializer_class = DomainRegistrantSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def get_queryset(self):
        """
        Filter registered domains on request user.
        :returns: Set of RegisteredDomain objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return DomainRegistrant.objects.all()
        return DomainRegistrant.objects.filter(registrant__person__owner=user)


class DomainHandleViewSet(viewsets.ModelViewSet):

    serializer_class = DomainHandlesSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def get_queryset(self):
        """
        Filter domain handles on logged in user.
        :returns: Set of DomainHandle objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return DomainHandles.objects.all()
        return DomainHandles.objects.filter(contact_handle__person__owner=user)