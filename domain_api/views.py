from __future__ import absolute_import, unicode_literals
import idna
from celery import chain, group
import logging
from django.db.models import Q
from django.shortcuts import get_object_or_404
# Remove this
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model
from rest_framework import status, permissions, viewsets, generics
from rest_framework.response import Response
from domain_api.models import (
    AccountDetail,
    ContactType,
    TopLevelDomain,
    DomainProvider,
    Registrant,
    Contact,
    RegisteredDomain,
    DomainContact,
    TopLevelDomainProvider,
    DefaultAccountTemplate,
    DefaultAccountContact,
    Nameserver,
)
from domain_api.serializers import (
    UserSerializer,
    AccountDetailSerializer,
    ContactTypeSerializer,
    ContactSerializer,
    TopLevelDomainSerializer,
    TopLevelDomainProviderSerializer,
    DomainProviderSerializer,
    RegistrantSerializer,
    RegisteredDomainSerializer,
    DomainAvailabilitySerializer,
    HostAvailabilitySerializer,
    DomainContactSerializer,
    PrivateInfoDomainSerializer,
    PrivateInfoContactSerializer,
    AdminInfoContactSerializer,
    DefaultAccountTemplateSerializer,
    DefaultAccountContactSerializer,
    InfoHostSerializer,
    AdminInfoHostSerializer,
    QueryInfoHostSerializer,
    PrivateInfoRegistrantSerializer,
    AdminInfoRegistrantSerializer,
    AdminInfoDomainSerializer,
    NameserverSerializer,
    AdminNameserverSerializer,
)
from domain_api.filters import (
    IsPersonFilterBackend
)
from .epp.queries import Domain as DomainQuery, ContactQuery, HostQuery
from .exceptions import (
    EppError,
    InvalidTld,
    UnsupportedTld,
    UnknownRegistry,
    DomainNotAvailable,
    NotObjectOwner,
    EppObjectDoesNotExist,
)
from domain_api.entity_management.contacts import (
    RegistrantManager,
    ContactManager
)
from domain_api.utilities.domain import (
    parse_domain,
    synchronise_domain,
    get_domain_registry,
    synchronise_host,
)
from .workflows import workflow_factory
from .permissions import IsAdmin
from application.settings import get_logzio_sender

log = logging.getLogger(__name__)


def get_registered_domain_queryset(user):
    """
    Return appropriate queryset depending on user roles.

    :user: User object
    :returns: RegisteredDomainQuerySet

    """
    queryset = RegisteredDomain.objects.all()
    if user.groups.filter(name='admin').exists():
        return queryset
    return queryset.filter(
        Q(registrant__user=user) |
        Q(contacts__contact__user=user)
    ).distinct()


def process_workflow_chain(chained_workflow):
    """
    Process results of workflow chain.

    :workflow_chain: chain workflow
    :returns: value of last item in chain

    """
    try:
        reversed_workflow = reversed(list(workflow_scan(chained_workflow)))
        values = [node.get() for node in reversed_workflow]
        return values[-1]
    except KeyError as e:
        log.error(str(e))
    except Exception as e:
        exception_type = type(e).__name__
        message = str(e)
        log.exception(message)
        if "DomainNotAvailable" in exception_type:
            raise DomainNotAvailable(message)
        elif "NotObjectOwner" in exception_type:
            raise NotObjectOwner(message)
        elif 'EppError' in exception_type:
            raise EppError(message)
        else:
            raise e


def workflow_scan(node):
    """
    Generate a list of workflow nodes.
    """
    while node.parent:
        yield node
        node = node.parent
    yield node


class CreateUserView(generics.CreateAPIView):
    """
    Create a user.
    """
    model = get_user_model()
    permission_classes = [permissions.AllowAny, ]
    serializer_class = UserSerializer

class BaseViewSet(viewsets.ModelViewSet):

    def is_admin(self):
        """
        Determine if the current logged in user is admin
        :returns: Boolean
        """
        user = self.request.user
        # Check if user is admin
        if user.groups.filter(name='admin').exists():
            return True
        return False

    def get_serializer_class(self):
        """
        Return serializer class for Nameserver
        """
        if self.is_admin():
            return self.admin_serializer_class
        return self.serializer_class


    def is_owner(self, obj):
        """
        Determine whether request user is owner of obj object.

        :obj: object
        :returns: Boolean

        """
        if obj.user == self.request.user:
            return True
        return False

    def get_queryset(self):
        """
        Return queryset
        :returns: queryset object

        """
        user = self.request.user
        if user.groups.filter(name='admin').exists():
            return self.queryset
        return self.queryset.filter(user=user).distinct()


class HostAvailabilityViewSet(viewsets.GenericViewSet):

    """
    Handle nameserver related queries.
    """

    serializer_class = HostAvailabilitySerializer
    permission_classes = [permissions.IsAuthenticated]

    def available(self, request, host=None):
        """
        Check availability of host.

        :request: HTTP request
        :returns: availability of host object

        """
        try:
            query = HostQuery()
            availability = query.check_host(
                idna.encode(host, uts46=True).decode('ascii')
            )
            serializer = HostAvailabilitySerializer(
                data=availability["result"][0]
            )
            if serializer.is_valid():
                return Response(serializer.data)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            log.error(str(e), exc_info=True)
            raise e


class DomainAvailabilityViewSet(viewsets.ViewSet):
    """
    Domain availability check endpoint
    """
    serializer_class = DomainAvailabilitySerializer
    permission_classes = (permissions.AllowAny,)

    def available(self, request, domain=None):
        """
        Check availability of a domain name

        :request: HTTP request
        :domain: str domain name to check
        :returns: availability of domain object

        """
        try:
            query = DomainQuery()
            availability = query.check_domain(
                idna.encode(domain, uts46=True).decode('ascii')
            )
            serializer = self.serializer_class(
                data=availability["result"][0]
            )
            if serializer.is_valid():
                return Response(serializer.data)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def bulk_available(self, request, name=None):
        """
        Leave the tld away to check availability at all supported tld providers.

        :request: HTTP request
        :name: str domain name to check
        :returns: availability of domain object

        """
        try:
            providers = DomainProvider.objects.filter(active=True)
            registry_workflows = []
            for provider in providers.all():
                provider_slug = provider.slug
                log.debug("Adding registry to check %s" % provider_slug)
                workflow_manager = workflow_factory(provider_slug)()
                tld_providers = provider.topleveldomainprovider_set.filter(
                    active=True
                )
                fqdn_list = []
                for tld_provider in tld_providers.all():
                    zone = tld_provider.zone.zone
                    fqdn_list.append(
                        ".".join(
                            [
                                idna.encode(name, uts46=True).decode('ascii'),
                                zone
                            ]
                        )
                    )
                    log.debug(
                        {
                            "msg": "Adding tld to check",
                            "tld": zone
                        }
                    )
                check_task = workflow_manager.check_domains(
                    fqdn_list
                )
                registry_workflows.append(check_task)
            check_group = group(registry_workflows)()
            registry_result = check_group.get()
            check_result = []
            for i in registry_result:
                check_result += i
            log.debug("Received check domain response")
            serializer = self.serializer_class(data=check_result,
                                               many=True)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AccountDetailViewSet(BaseViewSet):
    serializer_class = AccountDetailSerializer
    admin_serializer_class = AccountDetailSerializer
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly,)
    queryset = AccountDetail.objects.all()

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


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
    lookup_field = 'name'


class TopLevelDomainViewSet(viewsets.ModelViewSet):
    """
    Set of top level domains.
    """

    queryset = TopLevelDomain.objects.all()
    serializer_class = TopLevelDomainSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)
    lookup_field = "slug"


class DomainProviderViewSet(viewsets.ModelViewSet):
    """
    Set of tld providers.
    """

    queryset = DomainProvider.objects.all()
    serializer_class = DomainProviderSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)
    lookup_field = 'slug'


class ContactViewSet(BaseViewSet):
    """
    Contact handles.
    """

    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,
                          permissions.IsAuthenticated)
    filter_backends = (IsPersonFilterBackend,)
    lookup_field = 'registry_id'
    serializer_class = PrivateInfoContactSerializer
    admin_serializer_class = AdminInfoContactSerializer
    queryset = Contact.objects.all()

    def retrieve(self, request, registry_id=None):
        """
        Return a contact object.

        :request: HTTP Request object
        :registry_id: str id of contact or registrant
        :returns: Response object

        """
        queryset = self.get_queryset()
        contact = get_object_or_404(queryset, registry_id=registry_id)
        try:
            serializer_class = self.get_serializer_class()
            log.info("Serializer class: {!r}".format(serializer_class))
            log.debug("Performing info for %s as owner." % registry_id)
            query = ContactQuery(queryset)
            contact_data = query.info(contact)
            queryset.filter(pk=contact.id).update(**contact_data)
            contact = queryset.get(pk=contact.id)
            serializer = serializer_class(contact)
            return Response(serializer.data)
        except UnknownRegistry as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, registry_id=None):
        """
        PATCH update a domain

        :request: HTTPRequest
        :registry_id: str registry id
        :returns: Response object

        """
        contact = get_object_or_404(self.get_queryset(),
                                    registry_id=registry_id)
        if self.is_admin() or self.is_owner(contact):
            try:
                manager = self.manager(contact=registry_id)
                response = manager.update_contact(request.data)
                return Response(response)
            except Exception as e:
                log.error(str(e), exc_info=True)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_404_NOT_FOUND)


class RegistrantViewSet(ContactViewSet):

    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly,)
    lookup_field = 'registry_id'
    serializer_class = PrivateInfoRegistrantSerializer
    admin_serializer_class = AdminInfoRegistrantSerializer
    queryset = Registrant.objects.all()


class RegisteredDomainViewSet(BaseViewSet):

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = PrivateInfoDomainSerializer
    admin_serializer_class = AdminInfoDomainSerializer
    lookup_value_regex = '[^/]+'
    lookup_field = 'fqdn'

    def get_queryset(self):
        """
        Return queryset
        :returns: RegisteredDomain set
        """
        user = self.request.user
        queryset = get_registered_domain_queryset(user)
        registrant = self.request.query_params.get("registrant", None)
        if registrant is not None:
            queryset = queryset.filter(
                registrant__registry_id=registrant
            )
        admin = self.request.query_params.get("admin", None)
        if admin is not None:
            queryset = queryset.filter(
                contacts__contact__registry_id=admin,
                contacts__active=True
            )
        tech = self.request.query_params.get("tech", None)
        if tech is not None:
            queryset = queryset.filter(
                contacts__contact__registry_id=tech,
                contacts__active=True
            )
        nameserver = self.request.query_params.get("nameserver", None)
        if nameserver is not None:
            queryset = queryset.filter(
                nameservers__contains=nameserver
            )
        provider = self.request.query_params.get('provider', None)
        if provider is not None:
            queryset = queryset.filter(
                tld_provider__provider__slug=provider
            )
        return queryset

    def retrieve(self, request, fqdn=None):
        """
        Query EPP with a infoDomain request.


        :request: HTTP request
        :domain: str domain name to check
        :returns: JSON response with details about a domain

        """

        #registry = get_domain_registry(domain)
        #parsed_domain = parse_domain(domain)
        log.info("Looking for domain %s" % fqdn)
        queryset = self.get_queryset()
        registered_domain = get_object_or_404(
            queryset,
            fqdn=fqdn,
        )
        domain = registered_domain.name + "." + registered_domain.tld.zone

        try:
            # Fetch registry for domain
            query = DomainQuery(self.get_queryset())
            info = query.info(domain)
            get_logzio_sender().append(info)
            log.debug("Info domain for %s" % domain)
            serializer_class = self.get_serializer_class()
            synchronise_domain(info, registered_domain.id)
            serializer = serializer_class(
                queryset.get(pk=registered_domain.id)
            )
            return Response(serializer.data)
        except InvalidTld as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except UnsupportedTld as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except EppObjectDoesNotExist as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """
        Register a domain name.

        :request: Request object with JSON payload
        :returns: Response from registry
        """
        data = request.data
        parsed_domain = parse_domain(data["domain"])
        chain_res = None
        try:
            # See if this TLD is provided by one of our registries.
            tld_provider = TopLevelDomainProvider.objects.get(
                zone__zone=parsed_domain["zone"]
            )
            registry = tld_provider.provider.slug
            workflow_manager = workflow_factory(registry)()

            log.debug({"msg": "About to call workflow_manager.create_domain"})
            workflow = workflow_manager.create_domain(data, request.user)
            # run chained workflow and register the domain
            chained_workflow = chain(workflow)()
            chain_res = process_workflow_chain(chained_workflow)
            registered_domain = self.get_queryset().get(
                name=parsed_domain["domain"],
                tld__zone=parsed_domain["zone"],
                active=True
            )
            serializer = PrivateInfoDomainSerializer(registered_domain)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response("Registration error",
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except DomainNotAvailable as e:
            log.error(str(e), exc_info=True)
            return Response("Domain not available",
                            status=status.HTTP_400_BAD_REQUEST)
        except NotObjectOwner as e:
            log.error(str(e), exc_info=True)
            return Response("Not owner of object",
                            status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except TopLevelDomainProvider.DoesNotExist as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def partial_update(self, request, fqdn=None):
        """
        Partial update of domain

        :request: HTTP request object
        :pk: int primary key of domain
        :returns: Response object

        """
        queryset = self.get_queryset()
        registered_domain = get_object_or_404(
            queryset,
            fqdn=fqdn
        )
        domain = str(registered_domain)
        parsed_domain = parse_domain(domain)

        try:
            registry = registered_domain.tld_provider.provider.slug
            workflow_manager = workflow_factory(registry)()
            update_domain = request.data
            update_domain["domain"] = domain

            log.debug({"msg": "About to call workflow_manager.update_domain"})
            workflow = workflow_manager.update_domain(request.data,
                                                      registered_domain,
                                                      request.user)
            # run chained workflow and register the domain
            raw_workflow = chain(workflow)
            if not raw_workflow:
                return Response({"msg": "No change to domain"})
            chained_workflow = raw_workflow()
            chain_res = process_workflow_chain(chained_workflow)
            get_logzio_sender().append(chain_res)
            if registered_domain and self.is_admin_or_owner(registered_domain):
                serializer = self.serializer_class(
                    self.get_queryset().get(pk=registered_domain.id)
                )
                return Response(serializer.data)
        except EppObjectDoesNotExist as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class DomainContactViewSet(BaseViewSet):
    serializer_class = DomainContactSerializer
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly,)
    queryset = DomainContact.objects.all()


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):
    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.IsAdminUser,)

class DefaultAccountContactViewSet(viewsets.ModelViewSet):
    serializer_class = DefaultAccountContactSerializer
    permission_classes = (permissions.IsAdminUser,)
    queryset = DefaultAccountContact.objects.all()


class DefaultAccountTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = DefaultAccountTemplateSerializer
    permission_classes = (permissions.IsAuthenticated,)
    queryset = DefaultAccountTemplate.objects.all()


class NameserverViewSet(BaseViewSet):
    lookup_value_regex = '[^/]+'
    serializer_class = InfoHostSerializer
    admin_serializer_class = AdminInfoHostSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,
                          permissions.IsAuthenticated,)
    queryset = Nameserver.objects.all()
    lookup_field = 'idn_host'


    def get_registered_domain(self, host):
        """
        Retrieve registered domain for host. If the parent domain is not
        available to this user, throw an exception.

        :host: str host fqdn
        :returns: registered_domain instance

        """
        parsed_domain = parse_domain(host)
        domain_queryset = get_registered_domain_queryset(self.request.user)
        return domain_queryset.get(
            name=parsed_domain["domain"],
            tld__zone=parsed_domain["zone"],
            active=True
        )

    def retrieve(self, request, idn_host=None):
        """
        Return information about host

        :request: TODO
        :idn_host: TODO
        :returns: TODO

        """
        registered_host = get_object_or_404(
            self.get_queryset(),
            idn_host=idna.encode(idn_host, uts46=True).decode('ascii'),
        )
        try:
            # Fetch registry for host
            query = HostQuery(self.get_queryset())
            info = query.info(registered_host)
            self.get_queryset().filter(pk=registered_host.id).update(**info)
            registered_host = self.get_queryset().get(pk=registered_host.id)
            serializer_class = self.get_serializer_class()
            serializer = serializer_class(registered_host)
            return Response(serializer.data)
        except EppObjectDoesNotExist as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_404_NOT_FOUND)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request):
        """
        Register a nameserver host.

        :request: Request object with JSON payload
        :returns: Response from registry
        """
        data = request.data
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(data=data)
        get_logzio_sender().append(data)
        if serializer.is_valid():
            chain_res = None
            try:
                # Check that the domain parent exists and user has access to it.
                self.get_registered_domain(data["idn_host"])

                # See if this TLD is provided by one of our registries.
                registry = get_domain_registry(data["idn_host"])
                workflow_manager = workflow_factory(registry.slug)()
                log.debug("About to call workflow_manager.create_host")
                workflow = workflow_manager.create_host(data, request.user)
                # run chained workflow and register the domain
                chained_workflow = chain(workflow)()
                process_workflow_chain(chained_workflow)
                registered_host = self.get_queryset().get(
                    idn_host=idna.encode(data["idn_host"],
                                         uts46=True).decode('ascii'),
                )
                serializer = serializer_class(registered_host)
                return Response(serializer.data,
                                status=status.HTTP_201_CREATED)
            except InvalidTld as e:
                log.error(str(e), exc_info=True)
                return Response(status=status.HTTP_400_BAD_REQUEST)
            except RegisteredDomain.DoesNotExist:
                return Response({"host": data["host"],
                                 "msg": "Parent domain not available."},
                                status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                log.error(str(e), exc_info=True)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
