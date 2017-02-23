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
    Registrant,
    Contact,
    RegisteredDomain,
    DomainRegistrant,
    DomainContact,
    TopLevelDomainProvider
)
from domain_api.serializers import (
    UserSerializer,
    PersonalDetailSerializer,
    ContactTypeSerializer,
    ContactSerializer,
    TopLevelDomainSerializer,
    TopLevelDomainProviderSerializer,
    DomainProviderSerializer,
    RegistrantSerializer,
    DomainSerializer,
    RegisteredDomainSerializer,
    CheckDomainResponseSerializer,
    DomainRegistrantSerializer,
    DomainContactSerializer,
    InfoDomainSerializer,
    InfoContactSerializer,
)
from domain_api.filters import (
    IsPersonFilterBackend
)
from .epp.queries import Domain as DomainQuery, Contact as ContactQuery
from .exceptions import (
    EppError,
)
from domain_api.entity_management.contacts import ContactFactory
from domain_api.utilities.domain import parse_domain, get_domain_registry
from .workflows import workflow_factory


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def check_domain(request, domain, format=None):
    """
    Query EPP with a checkDomain request.
    :returns: JSON response indicating whether domain is available.
    """
    try:
        query = DomainQuery()
        provider = get_domain_registry(domain)
        availability = query.check_domain(provider.slug, domain)
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


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def info_contact(request, contact, format=None):
    """
    Query EPP with a infoContact request.
    :returns: JSON response with details about a contact

    """
    try:
        query = ContactQuery()
        info = query.info(contact)
        serializer = InfoContactSerializer(data=info)
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
            person = serializer.save(project_id=request.user)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    try:
        contact_factory = ContactFactory(provider,
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
            zone__zone=parsed_domain["zone"]
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
        serializer.save(project_id=self.request.user)

    def get_queryset(self):
        """
        Override to make sure that this only returns personal details that
        belong to logged in user.
        :returns: Filtered set of personal detail objects.

        """
        user = self.request.user
        if user.is_staff:
            return PersonalDetail.objects.all()
        return PersonalDetail.objects.filter(project_id=user)


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


class ContactViewSet(viewsets.ModelViewSet):
    """
    Contact handles.
    """

    serializer_class = ContactSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,
                          permissions.IsAuthenticated)
    filter_backends = (IsPersonFilterBackend,)

    def get_queryset(self):
        """
        Override to make sure that this only returns personal details that
        belong to logged in user.
        :returns: Filtered set of personal detail objects.

        """
        user = self.request.user
        if user.is_staff:
            return Contact.objects.all()
        return Contact.objects.filter(project_id=user)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.IsAdminUser,)


class RegistrantViewSet(viewsets.ModelViewSet):

    serializer_class = RegistrantSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        """
        Override to make sure that this only returns personal details that
        belong to logged in user.
        :returns: Filtered set of personal detail objects.

        """
        user = self.request.user
        if user.is_staff:
            return Registrant.objects.all()
        return Registrant.objects.filter(project_id=user)


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
        return DomainRegistrant.objects.filter(registrant__project_id=user)


class DomainContactViewSet(viewsets.ModelViewSet):

    serializer_class = DomainContactSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def get_queryset(self):
        """
        Filter domain handles on logged in user.
        :returns: Set of DomainContact objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return DomainContact.objects.all()
        return DomainContact.objects.filter(contact__project_id=user)
