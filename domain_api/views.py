from __future__ import absolute_import, unicode_literals
from celery import chain, group
from django_logging import log, ErrorLogObject
from django.db.models import Q
from django.shortcuts import get_object_or_404
# Remove this
from django.contrib.auth.models import User
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import (
    api_view,
    permission_classes,
    detail_route,
    list_route
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
    DefaultAccountTemplate
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
    DomainRegistrantSerializer,
    DomainContactSerializer,
    InfoDomainSerializer,
    InfoContactSerializer,
    DefaultAccountTemplateSerializer,
)
from domain_api.filters import (
    IsPersonFilterBackend
)
from .epp.queries import Domain as DomainQuery, ContactQuery
from .exceptions import (
    EppError,
    InvalidTld,
    UnsupportedTld,
    UnknownRegistry,
    DomainNotAvailable,
    NotObjectOwner,
    EppObjectDoesNotExist
)
from domain_api.entity_management.contacts import ContactFactory
from domain_api.utilities.domain import parse_domain, get_domain_registry
from .workflows import workflow_factory


def process_workflow_chain(chained_workflow):
    """
    Process results of workflow chain.

    :workflow_chain: chain workflow
    :returns: value of last item in chain

    """
    try:
        values = [node.get() for node in reversed(list(workflow_scan(chained_workflow)))]
        return values[-1]
    except KeyError as e:
        log.error({"keyerror": str(e)})
    except Exception as e:
        exception_type = type(e).__name__
        message = str(e)
        if "DomainNotAvailable" in exception_type:
            raise DomainNotAvailable(message)
        elif "NotObjectOwner" in exception_type:
            raise NotObjectOwner(message)
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
    queryset = AccountDetail.objects.all()
    if "person" in data:
        person = get_object_or_404(queryset, pk=data["person"])
    else:
        serializer = AccountDetailSerializer(data=data)
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


class ContactManagementViewSet(viewsets.GenericViewSet):
    """
    Handle contact related queries.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return the contact queryset.
        :returns: QuerySet object

        """
        user = self.request.user
        if self.request.user.groups.filter(name='admin').exists():
            return Contact.objects.all()
        return Contact.objects.filter(project_id=user)

    def info(self, request, registry_id, registry=None):
        """
        Retrieve info about a contact

        :request: HTTP request
        :registry_id: registry id
        :returns: InfoContactSerialised response

        """
        try:
            query = ContactQuery(request.user, self.get_queryset())
            info = query.info(registry_id, registry=registry)
            serializer = InfoContactSerializer(data=info)
            log.info(info)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except UnknownRegistry:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except EppError as epp_e:
            log.error(ErrorLogObject(request, epp_e))
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(ErrorLogObject(request, e))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def list(self, request):
        """
        List out contact/registrant objects

        :request: HTTP request object
        :returns: InfoContactSerizer response

        """
        contacts = self.get_queryset()
        serializer = InfoContactSerializer(contacts, many=True)
        return Response(serializer.data)

class RegistrantManagementViewSet(ContactManagementViewSet):
    """
    Handle registrant related queries.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Return the contact queryset.
        :returns: QuerySet object

        """
        user = self.request.user
        if self.request.user.groups.filter(name='admin').exists():
            return Registrant.objects.all()
        return Registrant.objects.filter(project_id=user)

class DomainRegistryManagementViewSet(viewsets.GenericViewSet):
    """
    Handle domain related queries.
    """
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = InfoDomainSerializer
    queryset = RegisteredDomain.objects.all()

    @detail_route(methods=['get'])
    def available(self, request, domain=None):
        """
        Check availability of a domain name

        :request: HTTP request
        :domain: str domain name to check
        :returns: availability of domain object

        """
        try:
            query = DomainQuery()
            provider = get_domain_registry(domain)
            availability = query.check_domain(provider.slug, domain)
            serializer = DomainAvailabilitySerializer(data=availability["result"][0])
            if serializer.is_valid():
                return Response(serializer.data)
        except EppError as epp_e:
            log.error(ErrorLogObject(request, epp_e))
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError as ke:
            log.error(ErrorLogObject(request, ke))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @detail_route(methods=['get'])
    def bulk_available(self, request, name=None):
        """
        Check availability of a domain name

        :request: HTTP request
        :name: str domain name to check
        :returns: availability of domain object

        """
        try:
            if "." in name:
                raise Exception("Not allowed to have a tld in bulk search")
            providers = DomainProvider.objects.all()
            registry_workflows = []
            for provider in providers.all():
                provider_slug = provider.slug
                workflow_manager = workflow_factory(provider_slug)()
                tld_providers = provider.topleveldomainprovider_set.all()
                fqdn_list = []
                for tld_provider in tld_providers.all():
                    zone = tld_provider.zone.zone
                    fqdn_list.append(".".join([name, zone]))
                check_task = workflow_manager.check_domains(
                    fqdn_list
                )
                registry_workflows.append(check_task)
            check_group = group(registry_workflows)()
            registry_result = check_group.get()
            check_result = []
            for i in registry_result:
                check_result += i
            log.info({"result": check_result})
            serializer = DomainAvailabilitySerializer(data=check_result, many=True)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)

        except EppError as epp_e:
            log.error(ErrorLogObject(request, epp_e))
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except KeyError as ke:
            log.error(ErrorLogObject(request, ke))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def domain_set(self, request):
        """
        Query for domains linked to a particular registry contact
        :returns: JSON response with details about a contact

        """
        try:
            # Limit registered domain query to "owned" domains
            registered_domain_set = self.get_queryset().filter(
                Q(registrant__registrant__project_id=request.user) |
                Q(contacts__contact__project_id=request.user)
            ).distinct()
            # Admin gets access to all domains.
            if request.user.groups.filter(name='admin').exists():
                registered_domain_set = self.get_queryset()

            contact_domains = registered_domain_set
            if len(contact_domains) == 0:
                return Response(status=status.HTTP_400_BAD_REQUEST)
            domain_set = []
            for domain in contact_domains.filter(active=True):
                domain_object = {}
                domain_object["domain"] = ".".join([domain.domain.name,
                                                    domain.tld.zone])
                domain_object["registrant"] = domain.registrant.first().registrant.registry_id
                contact_set = []
                for dom_contact in domain.contacts.all():
                    domain_contact = {}
                    domain_contact[dom_contact.contact_type.name] = dom_contact.contact.registry_id
                    contact_set.append(domain_contact)
                domain_object["contacts"] = contact_set
                domain_object["ns"] = []
                domain_object["anniversary"] = domain.anniversary
                domain_object["created"] = domain.created
                domain_set.append(domain_object)

            serializer = InfoDomainSerializer(data=domain_set, many=True)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(ErrorLogObject(request, e))
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
            provider = get_domain_registry(domain)

            query = DomainQuery()
            info = query.info(domain, provider.slug, user=request.user)
            serializer = InfoDomainSerializer(data=info)
            log.info(info)
            if serializer.is_valid():
                return Response(serializer.data)
            else:
                return Response(serializer.errors,
                                status=status.HTTP_400_BAD_REQUEST)
        except InvalidTld as e:
            log.error(ErrorLogObject(request, e))
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except UnsupportedTld as e:
            log.error(ErrorLogObject(request, e))
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except EppObjectDoesNotExist as epp_e:
            log.error(ErrorLogObject(request, epp_e))
            return Response(status=status.HTTP_404_NOT_FOUND)
        except EppError as epp_e:
            log.error(ErrorLogObject(request, epp_e))
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(ErrorLogObject(request, e))
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
                return Response(serializer.data)
            else:
                log.error(serializer.errors)
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response(chain_res)
        except DomainNotAvailable:
            return Response("Domain not available",
                            status=status.HTTP_400_BAD_REQUEST)
        except NotObjectOwner:
            return Response("Not owner of object",
                            status=status.HTTP_400_BAD_REQUEST)
        except KeyError as e:
            log.error(ErrorLogObject(request, e))
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except TopLevelDomainProvider.DoesNotExist:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(ErrorLogObject(request, e))
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
    lookup_field = 'slug'


class ContactViewSet(viewsets.ModelViewSet):
    """
    Contact handles.
    """

    serializer_class = ContactSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,
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
    permission_classes = (permissions.IsAuthenticated,)
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
    permission_classes = (permissions.IsAuthenticated,)
    queryset = Domain.objects.all()


class RegisteredDomainViewSet(viewsets.ModelViewSet):

    serializer_class = RegisteredDomainSerializer
    permission_classes = (permissions.IsAuthenticated,
                          permissions.DjangoModelPermissionsOrAnonReadOnly,)
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

        :request: TODO
        :data: TODO
        :returns: TODO

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


    def delete(self, request, default_id):
        """
        Delete a default template

        :request: TODO
        :default_id: TODO
        :returns: TODO

        """
        default_account_template = get_object_or_404(self.get_queryset(),
                                                     pk=default_id)
        default_account_template.delete()

    def detail(self, request, default_id):
        """
        Retrieve single object

        :request: TODO
        :default_id: TODO
        :returns: TODO

        """
        log.debug({"default_id": default_id})
        default_account_template = get_object_or_404(self.get_queryset(),
                                                     pk=default_id)
        serializer = self.serializer_class(default_account_template,
                                           context={"request": request})
        return Response(serializer.data)

    def list(self, request):
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

    #def perform_create(self, serializer):

        #data = self.request.data
        #provider_slug = data["provider"]
        #provider = DomainProvider.objects.get(slug=provider_slug)
        #serializer.save(project_id=self.request.user, provider=provider)
