from django_logging import log, ErrorLogObject
import requests
import json
from encodings import idna
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
    DomainRegistrantSerializer,
    DomainHandlesSerializer,
)
from domain_api.filters import (
    IsOwnerFilterBackend,
    IsPersonFilterBackend
)


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def check_domain(request, domain, format=None):
    """
    Query EPP with a checkDomain request.
    :returns: JSON response indicating whether domain is available.

    """
    request_data = {"domain": domain}
    response = requests.post('http://centralnic:3000/command/centralnic-test/checkDomain',
                             headers={"Content-type": "application/json"},
                             data=json.dumps(request_data))

    response_data = response.json()
    try:
        available = response_data["data"]["domain:chkData"]["domain:cd"]["domain:name"]["avail"]
        log.error("Got response data %s" % available)
        is_available = False
        if available and (available == 1 or available == "1") :
            is_available = True
        availability = {"result": [{"domain": domain, "available": is_available}]}
        serializer = CheckDomainResponseSerializer(data=availability)
        if serializer.is_valid():
            return Response(serializer.data)
    except KeyError:
        raise

@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
def registry_contact(request, registry, person_id=None):
    """
    Create or view contacts for a particular registry.

    :registry: Registry to add this contact for
    :person_id: Optional person object
    :returns: A contact object

    """

    log.debug("Request for registry contact")
    if request.method == 'GET':
        try:
            if request.user.is_staff:
                contacts = ContactHandle.objects.filter(provider__slug=registry)
            else:
                contacts = ContactHandle.objects.filter(provider__slug=registry, person__owner=request.user)
            serializer = ContactHandleSerializer(contacts, many=True, context={"request": request})
            return Response(serializer.data)
        except ContactHandle.DoesNotExist:
            raise Http404
    elif request.method == 'POST':

        data = request.data
        log.debug(data)
        serializer = PersonalDetailSerializer(data=data)
        if serializer.is_valid():
            person = serializer.save(owner=request.user)
        else:
            raise Exception("Unable to save person.")
        handle = "api-test-" + str(person.id)
        street = [person.street1, person.street2, person.street3]
        postal_info = {
            "name": person.first_name + " " + person.surname,
            "org": person.company,
            "type": "int",
            "addr" : {
                "street": street,
                "city": person.city,
                "sp": person.state,
                "pc": person.postcode,
                "cc": person.country
            }
        }
        contact_info = {
            "id": handle,
            "voice": person.telephone,
            "fax": person.fax,
            "email": person.email,
            "postalInfo": postal_info
        }
        response = requests.post('http://centralnic:3000/command/centralnic-test/createContact',
                                headers={"Content-type": "application/json"},
                                data=json.dumps(contact_info))

        # Raise an error if this didn't work
        response.raise_for_status()
        provider = DomainProvider.objects.get(slug=registry)
        contact_handle = person.contacthandle_set.create(handle=handle,
                                                         provider=provider,
                                                         owner=request.user)
        serializer = ContactHandleSerializer(contact_handle, context={'request': request})

        return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
def registrant(request, registry, person_id=None):
    """
    Create or view a registrant for a particular registry.

    :registry: Registry to add this registrant for
    :person_id: Optional person object
    :returns: A contact object

    """

    log.debug("Request for registrant")
    if request.method == 'GET':
        try:
            if request.user.is_staff:
                contacts = RegistrantHandle.objects.filter(provider__slug=registry)
            else:
                contacts = RegistrantHandle.objects.filter(provider__slug=registry, person__owner=request.user)
            serializer = RegistrantHandleSerializer(contacts, many=True, context={"request": request})
            return Response(serializer.data)
        except RegistrantHandle.DoesNotExist:
            raise Http404
    elif request.method == 'POST':

        data = request.data
        log.debug(data)
        serializer = PersonalDetailSerializer(data=data)
        if serializer.is_valid():
            person = serializer.save(owner=request.user)
        else:
            raise Exception("Unable to save person.")
        handle = "api-test-" + str(person.id)
        street = [person.street1, person.street2, person.street3]
        postal_info = {
            "name": person.first_name + " " + person.surname,
            "org": person.company,
            "type": "int",
            "addr" : {
                "street": street,
                "city": person.city,
                "sp": person.state,
                "pc": person.postcode,
                "cc": person.country
            }
        }
        contact_info = {
            "id": handle,
            "voice": person.telephone,
            "fax": person.fax,
            "email": person.email,
            "postalInfo": postal_info
        }
        response = requests.post('http://centralnic:3000/command/centralnic-test/createContact',
                                 headers={"Content-type": "application/json"},
                                 data=json.dumps(contact_info))

        # Raise an error if this didn't work
        response.raise_for_status()
        provider = DomainProvider.objects.get(slug=registry)
        contact_handle = person.registranthandle_set.create(handle=handle,
                                                            provider=provider,
                                                            owner=request.user)
        serializer = RegistrantHandleSerializer(contact_handle, context={'request': request})

        return Response(serializer.data)


@api_view(['POST'])
@permission_classes((permissions.IsAuthenticated,))
def register_domain(request):
    """
    Register a domain name.

    :request: Request object with JSON payload
    :returns: Response from registry

    """
    data = request.data
    registrant = RegistrantHandle.objects.get(pk=data['registrant'])
    admin = ContactHandle.objects.get(pk=data['admin'])
    tech = ContactHandle.objects.get(pk=data['tech'])
    domain = data["domain"]
    tlds = TopLevelDomain.objects.all()
    probable_tld = None
    length = 0
    domain_name = None
    for tld in tlds:
        zone = "." + tld.zone
        endindex = - (len(zone))
        if zone == domain[endindex:] and len(zone) > length:
            probable_tld = tld
            length = len(zone)
            # Get the actual domain name. Make sure it doesn't have
            # any subdomain prefixed
            domain_name = domain[:endindex].split(".")[-1]
    # Some possible error scenarios
    if probable_tld is None:
        log.error("Unsupported tld in domain %s" % domain)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    if domain_name is None or len(domain_name) == 0:
        log.error("Probably an invalid domain name %s" % domain)
        return Response(status=status.HTTP_400_BAD_REQUEST)
    try:
        # See if this TLD is provided by one of our registries.
        tld_provider = TopLevelDomainProvider.objects.get(zone=probable_tld)
    except TopLevelDomainProvider.DoesNotExist as e:
        log.error(ErrorLogObject(request, e))
        return Response(status=status.HTTP_400_BAD_REQUEST)
    register_zone = probable_tld.zone
    try:
        domain_obj = Domain.objects.get(name=domain_name)
    except Domain.DoesNotExist:
        domain_obj = Domain(name=domain_name,
               idn=idna.ToASCII(domain_name),
               owner=request.user)
        domain_obj.save()

    epp_request = {
        "name": data["domain"],
        "registrant": registrant.handle,
        "contact": [
            {"admin": admin.handle},
            {"tech": tech.handle}
        ],
        "ns": [
            "ns1.hexonet.net",
            "ns2.hexonet.net"
        ]
    }
    log.info(epp_request)
    response = requests.post('http://centralnic:3000/command/centralnic-test/createDomain',
                            headers={"Content-type": "application/json"},
                            data=json.dumps(epp_request))

    # Raise an error if this didn't work
    response.raise_for_status()
    try:
        response_data = response.json()
        result_code = response_data["result"]["code"]
        if int(result_code) >= 2000:
            log.error(response_data["result"]["msg"])
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        anniversary_field = response_data["data"]["domain:creData"]["domain:exDate"]
        registered_domain = RegisteredDomain(domain=domain_obj,
                                             tld=probable_tld,
                                             tld_provider=tld_provider,
                                             registration_period=1,
                                             anniversary=anniversary_field,
                                             owner=request.user,
                                             active=True)
        registered_domain.save()
        admin_contact_type = ContactType.objects.get(name='admin')
        tech_contact_type = ContactType.objects.get(name='tech')
        registered_domain.domainregistrant_set.create(
            registrant=registrant,
            active=True,
            owner=request.user
        )
        registered_domain.domainhandles_set.create(
            contact_handle=admin,
            active=True,
            contact_type=admin_contact_type,
            owner=request.user
        )
        registered_domain.domainhandles_set.create(
            contact_handle=tech,
            active=True,
            contact_type=tech_contact_type,
            owner=request.user
        )

    except Exception as e:
        log.error(ErrorLogObject(request, e))
        raise e
    log.info(response.json())

    return Response(status=status.HTTP_204_NO_CONTENT)




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

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomain.objects.all()
    serializer_class = TopLevelDomainSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DomainProviderViewSet(viewsets.ModelViewSet):

    queryset = DomainProvider.objects.all()
    serializer_class = DomainProviderSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ContactHandleViewSet(viewsets.ModelViewSet):

    serializer_class = ContactHandleSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,
                          permissions.IsAuthenticated)
    queryset = ContactHandle.objects.all()
    filter_backends = (IsPersonFilterBackend,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class RegistrantHandleViewSet(viewsets.ModelViewSet):

    serializer_class = RegistrantHandleSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """
        Override to make sure that this only returns personal details that belong to logged in user.
        :returns: Filtered set of personal detail objects.

        """
        user = self.request.user
        if user.is_staff:
            return RegistrantHandle.objects.all()
        return RegistrantHandle.objects.filter(person__owner=user)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class DomainViewSet(viewsets.ModelViewSet):

    serializer_class = DomainSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """
        Filter the queryset for the logged in user.
        :returns: Domain objects filtered by user.

        """
        user = self.request.user
        if user.is_staff:
            return Domain.objects.all()
        return Domain.objects.filter(owner=user)


class RegisteredDomainViewSet(viewsets.ModelViewSet):

    serializer_class = RegisteredDomainSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """
        Filter registered domains on request user.
        :returns: Set of RegisteredDomain objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return RegisteredDomain.objects.all()
        return RegisteredDomain.objects.filter(domain__owner=user)


class DomainRegistrantViewSet(viewsets.ModelViewSet):

    serializer_class = DomainRegistrantSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

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

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def get_queryset(self):
        """
        Filter domain handles on logged in user.
        :returns: Set of DomainHandle objects filtered by customer

        """
        user = self.request.user
        if user.is_staff:
            return DomainHandles.objects.all()
        return DomainHandles.objects.filter(contact_handle__person__owner=user)
