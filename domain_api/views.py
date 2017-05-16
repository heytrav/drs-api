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
from rest_framework.decorators import (
    detail_route,
)
from rest_framework.response import Response
from domain_api.models import (
    Domain,
    AccountDetail,
    ContactType,
    TopLevelDomain,
    DomainProvider,
    Registrant,
    Contact,
    RegisteredDomain,
    DomainRegistrant,
    DomainContact,
    TopLevelDomainProvider,
    DefaultAccountTemplate,
    NameserverHost,
    DefaultAccountContact,
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
    DomainSerializer,
    RegisteredDomainSerializer,
    DomainAvailabilitySerializer,
    HostAvailabilitySerializer,
    DomainRegistrantSerializer,
    DomainContactSerializer,
    InfoDomainSerializer,
    PrivateInfoDomainSerializer,
    InfoContactSerializer,
    PrivateInfoContactSerializer,
    DefaultAccountTemplateSerializer,
    InfoHostSerializer,
    PrivateInfoHostSerializer,
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
    EppObjectDoesNotExist
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
        Q(registrant__registrant__project_id=user) |
        Q(contacts__contact__project_id=user)
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


class ContactManagementViewSet(viewsets.GenericViewSet):
    """
    Handle contact related queries.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateInfoContactSerializer
    queryset = Contact.objects.all()
    manager = ContactManager

    def is_admin_or_owner(self, contact=None):
        """
        Determine if the current logged in user is admin or the owner of
        the object.

        :contact: Contact/Registrant object
        :returns: True or False

        """
        if self.request.user.groups.filter(name='admin').exists():
            log.debug("Is admin")
            return True
        if contact and contact.project_id == self.request.user:
            log.debug("User owns %s " % contact.registry_id)
            return True
        return False

    def get_disclosed_contact_data(self, contact):
        """
        Prepare data to be returned with request. Check if dislosure is allowed.

        :contact: Contact object
        :returns: dict containing contact attributes allowed for disclosure

        """
        contact_data = {
            "registry_id": contact.registry_id,
        }
        if contact.disclose_name:
            contact_data["name"] = contact.name
        if contact.disclose_email:
            contact_data["email"] = contact.email
        if contact.disclose_telephone:
            contact_data["telephone"] = contact.telephone
        if contact.disclose_fax:
            contact_data["fax"] = contact.fax
        if contact.disclose_company:
            contact_data["company"] = contact.company
        if contact.disclose_address:
            contact_data["street1"] = contact.street1
            contact_data["street2"] = contact.street2
            contact_data["street3"] = contact.street3
            contact_data["city"] = contact.city
            contact_data["house_number"] = contact.house_number
            contact_data["country"] = contact.country
            contact_data["state"] = contact.state
            contact_data["postcode"] = contact.postcode
            contact_data["postal_info_type"] = contact.postal_info_type
        return contact_data

    def info(self, request, registry_id, registry=None):
        """
        Retrieve info about a contact

        :request: HTTP request
        :registry_id: registry id
        :returns: InfoContactSerialised response

        """
        try:
            contact = self.get_queryset().get(registry_id=registry_id)

            if self.is_admin_or_owner(contact):
                log.debug("Performing info for %s as owner." % registry_id)
                query = ContactQuery(self.get_queryset())
                contact = query.info(contact)
                serializer = self.serializer_class(contact)
                return Response(serializer.data)
            else:
                log.debug("Basic contact query for %s" % registry_id)
                contact_data = self.get_disclosed_contact_data(contact)
                serializer = InfoContactSerializer(data=contact_data)
                if serializer.is_valid():
                    log.debug("Serialized data is valid.")
                    return Response(serializer.data)
                else:
                    return_data = {
                        "message": "Serialized data is not valid.",
                        "data": contact_data
                    }
                    get_logzio_sender().append(return_data)
                    log.warning("Serialized data is not valid.")
                    return Response(serializer.errors)

        except UnknownRegistry as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except EppError as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, registry_id):
        """
        Update a contact object

        :request: HTTP request
        :registry_id: registry id
        :registry: str registry to perform update at

        """
        contact = get_object_or_404(self.queryset, registry_id=registry_id)
        if self.is_admin_or_owner(contact):
            try:
                manager = self.manager(contact=registry_id)
                response = manager.update_contact(request.data)
                return Response(response)
            except Exception as e:
                log.error(str(e), exc_info=True)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(status=status.HTTP_404_NOT_FOUND)

    def list_contacts(self, request):
        """
        List out contact/registrant objects

        :request: HTTP request object
        :returns: InfoContactSerializer response

        """
        contacts = self.get_queryset()
        if not self.is_admin_or_owner():
            contacts = contacts.filter(project_id=self.request.user)

        serializer = InfoContactSerializer(contacts, many=True)
        return Response(serializer.data)


class RegistrantManagementViewSet(ContactManagementViewSet):
    """
    Handle registrant related queries.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateInfoContactSerializer
    queryset = Registrant.objects.all()
    manager = RegistrantManager


class HostManagementViewSet(viewsets.GenericViewSet):

    """
    Handle nameserver related queries.
    """

    serializer_class = InfoHostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def is_admin_or_owner(self, host=None):
        """
        Determine if the current logged in user is admin or the owner of
        the object.

        :domain: Contact/Registrant object
        :returns: True or False

        """
        user = self.request.user
        # Check if user is admin
        if user.groups.filter(name='admin').exists():
            return True
        # otherwise check if user is registrant of contact for domain
        if host:
            if host.project_id == user:
                return True
        return False

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
            domain__name=parsed_domain["domain"],
            tld__zone=parsed_domain["zone"],
            active=True
        )

    def get_queryset(self):
        """
        Return queryset
        :returns: queryset object

        """
        queryset = NameserverHost.objects.all()
        user = self.request.user
        if user.groups.filter(name='admin').exists():
            return queryset
        return queryset.filter(project_id=user).distinct()

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

    def host_set(self, request):
        """
        Query for domains linked to a particular registry contact
        :returns: JSON response with details about a contact

        """
        try:
            # Limit registered domain query to "owned" domains
            hosts = self.get_queryset().filter()
            serializer = PrivateInfoHostSerializer(hosts, many=True)
            return Response(serializer.data)
        except Exception:
            log.error("", exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def info(self, request, host):
        """
        Query EPP with a infoHost request.

        :request: HTTP request
        :host: str host name to check
        :returns: JSON response with details about a host
        """
        try:
            # Fetch registry for host
            query = HostQuery(self.get_queryset())
            info, registered_host = query.info(host)
            if registered_host and self.is_admin_or_owner(registered_host):
                synchronise_host(info, registered_host.id)
                serializer = PrivateInfoHostSerializer(
                    self.get_queryset().get(pk=registered_host.id)
                )
                return Response(serializer.data)
            serializer = InfoHostSerializer(data=info)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
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
        serializer = self.serializer_class(data=data)
        get_logzio_sender().append(data)
        if serializer.is_valid():
            chain_res = None
            try:
                # Check that the domain parent exists and user has access to it.
                self.get_registered_domain(data["host"])

                # See if this TLD is provided by one of our registries.
                registry = get_domain_registry(data["host"])
                workflow_manager = workflow_factory(registry.slug)()

                log.debug("About to call workflow_manager.create_host")
                workflow = workflow_manager.create_host(data, request.user)
                # run chained workflow and register the domain
                chained_workflow = chain(workflow)()
                chain_res = process_workflow_chain(chained_workflow)
                serializer = InfoHostSerializer(data=chain_res)
                if serializer.is_valid():
                    return Response(serializer.data,
                                    status=status.HTTP_201_CREATED)
                else:
                    log.error("Error serializing data")
                    return Response(
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR
                    )
                return Response(chain_res)
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


class DomainRegistryManagementViewSet(viewsets.GenericViewSet):
    """
    Handle domain related queries.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = PrivateInfoDomainSerializer

    def get_queryset(self):
        """
        Return queryset
        :returns: RegisteredDomain set
        """
        user = self.request.user
        return get_registered_domain_queryset(user)

    def is_admin_or_owner(self, domain=None):
        """
        Determine if the current logged in user is admin or the owner of
        the object.

        :domain: Registered domain object
        :returns: True or False

        """
        user = self.request.user
        # Check if user is admin
        if user.groups.filter(name='admin').exists():
            return True
        # otherwise check if user is registrant of contact for domain
        if domain:
            if domain.registrant.filter(
                active=True,
                registrant__project_id=user
            ):
                return True
            if domain.contacts.filter(contact__project_id=user).exists():
                return True
        return False

    def domain_set(self, request):
        """
        Query for domains linked to a particular registry contact
        :returns: JSON response with details about a contact

        """
        try:
            # Limit registered domain query to "owned" domains
            registered_domain_set = self.get_queryset()
            contact_domains = registered_domain_set.filter(active=True)
            serializer = self.serializer_class(contact_domains, many=True)
            return Response(serializer.data)
        except Exception as e:
            log.error(str(e), exc_info=True)
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def info(self, request, domain):
        """
        Query EPP with a infoDomain request.


        :request: HTTP request
        :domain: str domain name to check
        :returns: JSON response with details about a domain

        """
        try:
            # Fetch registry for domain
            query = DomainQuery(self.get_queryset())
            info, registered_domain = query.info(domain)
            get_logzio_sender().append(info)
            log.debug("Info domain for %s" % domain)
            if registered_domain and self.is_admin_or_owner(registered_domain):
                synchronise_domain(info, registered_domain.id)
                serializer = self.serializer_class(
                    self.get_queryset().get(pk=registered_domain.id)
                )
                return Response(serializer.data)
            serializer = InfoDomainSerializer(data=info)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
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
            serializer = InfoDomainSerializer(data=chain_res)
            if serializer.is_valid():
                return Response(serializer.data, status=status.HTTP_201_CREATED)
            else:
                log.error(serializer.errors)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(chain_res)
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


class AccountDetailViewSet(viewsets.ModelViewSet):
    serializer_class = AccountDetailSerializer
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
            return AccountDetail.objects.all()
        return AccountDetail.objects.filter(project_id=user)


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


class ContactViewSet(viewsets.ModelViewSet):
    """
    Contact handles.
    """

    serializer_class = ContactSerializer
    permission_classes = (permissions.IsAdminUser,
                          permissions.IsAuthenticated)
    filter_backends = (IsPersonFilterBackend,)
    lookup_field = 'registry_id'

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
    permission_classes = (permissions.IsAuthenticated,
                          permissions.IsAdminUser)
    lookup_field = 'registry_id'

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
    permission_classes = (permissions.IsAuthenticated,
                          IsAdmin,)
    queryset = Domain.objects.all()
    lookup_field = 'name'


class RegisteredDomainViewSet(viewsets.ModelViewSet):

    serializer_class = RegisteredDomainSerializer
    permission_classes = (permissions.IsAuthenticated,
                          IsAdmin,)
    queryset = RegisteredDomain.objects.all()


class DomainRegistrantViewSet(viewsets.ModelViewSet):

    serializer_class = DomainRegistrantSerializer
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly,)

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
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def get_queryset(self):
        """
        Filter domain handles on logged in user.
        :returns: Set of DomainContact objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return DomainContact.objects.all()
        return DomainContact.objects.filter(contact__project_id=user)


class DefaultAccountTemplateViewSet(viewsets.ModelViewSet):
    serializer_class = DefaultAccountTemplateSerializer
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly)

    def create(self, request):
        """
        Create a new default template

        :request: HTTP request object
        :returns: HTTP response

        """
        data = request.data
        serializer = self.serializer_class(data=data)
        if serializer.is_valid():
            account_templates = AccountDetail.objects.filter(
                project_id=request.user
            )
            account_template = get_object_or_404(account_templates,
                                                 pk=data["account_template"])
            serializer.save(
                project_id=request.user,
                account_template=account_template,
                provider=DomainProvider.objects.get(slug=data["provider"])
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, default_id):
        """
        Update a default account template

        """
        default_account_template = get_object_or_404(self.get_queryset(),
                                                     default_id)
        data = request.data
        account_templates = AccountDetail.objects.filter(
            project_id=request.user
        )
        account_template = get_object_or_404(account_templates,
                                             pk=data["account_template"])
        default_account_template.update(account_template=account_template,
                                        provider=data["provider"])

    def delete_account(self, request, default_id):
        """
        Delete a default template

        """
        default_account_template = get_object_or_404(self.get_queryset(),
                                                     pk=default_id)
        default_account_template.delete()

    def detail(self, request, default_id):
        """
        Retrieve single object

        """
        log.debug({"default_id": default_id})
        default_account_template = get_object_or_404(self.get_queryset(),
                                                     pk=default_id)
        serializer = self.serializer_class(default_account_template,
                                           context={"request": request})
        return Response(serializer.data)

    def list_accounts(self, request):
        """
        Return list of default accounts

        :request: HTTP request object
        :returns: DefaultAccountTemplateSerializer

        """
        account_templates = self.get_queryset()
        serializer = self.serializer_class(account_templates,
                                           context={"request": request},
                                           many=True)
        return Response(serializer.data)

    def get_queryset(self):
        """
        Filter domain handles on logged in user.
        :returns: Set of DomainContact objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return DefaultAccountTemplate.objects.all()
        return DefaultAccountTemplate.objects.filter(project_id=user)


class DefaultAccountContactViewSet(viewsets.ModelViewSet):
    serializer_class = DefaultAccountTemplateSerializer
    permission_classes = (permissions.IsAdminUser,)

    def get_queryset(self):
        """
        Filter domain handles on logged in user.
        :returns: Set of DomainContact objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return DefaultAccountContact.objects.all()
        return DefaultAccountContact.objects.filter(project_id=user)
