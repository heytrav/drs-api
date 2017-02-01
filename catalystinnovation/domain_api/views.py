import os
from django_logging import log, ErrorLogObject
from django.db import IntegrityError
from django.shortcuts import get_object_or_404
import requests
import json
from encodings import idna
from django.contrib.auth.models import User
from django.http import Http404
from rest_framework import status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from domain_api.models import (
    PersonalDetail,
    ContactType,
    TopLevelDomain,
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
    InfoDomainSerializer,
)
from domain_api.filters import (
    IsPersonFilterBackend
)
from .utilities.rpc_client import EppRpcClient

rabbit_host = os.environ.get('RABBIT_HOST')

@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def check_domain(request, registry, domain, format=None):
    """
    Query EPP with a checkDomain request.
    :returns: JSON response indicating whether domain is available.

    """
<<<<<<< HEAD
    response = requests.get('http://centralnic:3000/checkDomain/' + domain,
                            headers={"Content-type": "application/json"})

    response_data = response.json()
=======
    rpc_client = EppRpcClient(host=rabbit_host)
    data = {"command": "checkDomain", "domain": domain}
    response_data = rpc_client.call('epp', registry, json.dumps(data))
    log.debug(response_data)
>>>>>>> Switch to rabbitmq for interaction with EPP service
    try:
        available = response_data["data"]["domain:chkData"]["domain:cd"]["domain:name"]["avail"]
        log.error("Got response data %s" % available)
        is_available = False
        if available and (available == 1 or available == "1"):
            is_available = True
        availability = {
            "result": [
                {
                    "domain": domain,
                    "available": is_available
                }
            ]
        }
        serializer = CheckDomainResponseSerializer(data=availability)
        if serializer.is_valid():
            return Response(serializer.data)
    except KeyError:
        raise


@api_view(['GET'])
@permission_classes((permissions.IsAuthenticated,))
def info_domain(request, registry, domain, format=None):
    """
    Query EPP with a infoDomain request.
    :returns: JSON response with details about a domain

    """
    rpc_client = EppRpcClient(host=rabbit_host)
    data = {"command": "infoDomain", "domain": domain}
    epp_response = rpc_client.call('epp', registry, json.dumps(data))
    log.debug(epp_response)
    try:
        if int(epp_response["result"]["code"]) >= 2000:
            log.error(epp_response)
            return Response(status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        log.error(ErrorLogObject(request, e))
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    try:
        response_data = epp_response["data"]["domain:infData"]
        for contact in response_data["domain:contact"]:
            if '$t' in contact:
                contact["handle"] = contact["$t"]
                contact["contact_type"] = contact["type"]
                del contact["type"]
                del contact["$t"]
        return_data = {
            "domain": response_data["domain:name"],
            "status": response_data["domain:status"],
            "registrant": response_data["domain:registrant"],
            "contacts": response_data["domain:contact"],
            "ns": response_data["domain:ns"]["domain:hostObj"],
        }
        if request.user.is_staff:
            return_data["auth_info"] = response_data["domain:authInfo"]["domain:pw"]
            return_data["roid"] = response_data["domain:roid"]
        log.info(return_data)
        serializer = InfoDomainSerializer(data=return_data)
        if serializer.is_valid():
            return Response(serializer.data)
        else:
            log.error(serializer.errors)
    except Exception as e:
        log.error(ErrorLogObject(request, e))
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
def registry_contact(request, registry):
    """
    Create or view contacts for a particular registry.

    :registry: Registry to add this contact for
    :person_id: Optional person object
    :returns: A contact object

    """

    provider = get_object_or_404(DomainProvider.objects.all(), slug=registry)
    if request.method == 'GET':
        try:
            if request.user.is_staff:
                contacts = ContactHandle.objects.filter(provider__slug=registry)
            else:
                contacts = ContactHandle.objects.filter(
                    provider__slug=registry,
                    person__owner=request.user
                )
            serializer = ContactHandleSerializer(contacts,
                                                 many=True,
                                                 context={"request": request})
            return Response(serializer.data)
        except ContactHandle.DoesNotExist:
            raise Http404
    elif request.method == 'POST':

        data = request.data
        log.debug(data)
        person = None
        queryset = PersonalDetail.objects.filter(owner=request.user)
        if request.user.is_staff:
            queryset = PersonalDetail.objects.all()
        if "person" in data:
<<<<<<< HEAD
            person = get_object_or_404(PersonalDetail.objects.all(),
                                       pk=data["person"])
=======
            person = get_object_or_404(queryset, pk=data["person"])
>>>>>>> Switch to rabbitmq for interaction with EPP service
        else:
            serializer = PersonalDetailSerializer(data=data)
            if serializer.is_valid():
                person = serializer.save(owner=request.user)
            else:
                raise Exception("Unable to save person.")
        #  Hacky way to generate a handle
        handle = "-".join(["test", "api", str(person.id), str(ContactHandle.objects.count() + 1)])
        street = [person.street1, person.street2, person.street3]
        postal_info = {
            "name": person.first_name + " " + person.surname,
            "org": person.company,
            "type": "int",
            "addr": {
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
<<<<<<< HEAD
        response = requests.post('http://centralnic:3000/createContact',
                                 headers={"Content-type": "application/json"},
                                 data=json.dumps(contact_info))
=======
        rpc_client = EppRpcClient(host=rabbit_host)
        contact_info['command'] = 'createContact'
        epp_response = rpc_client.call('epp', registry, json.dumps(contact_info))
        try:
            if int(epp_response["result"]["code"]) >= 2000:
                log.error(epp_response)
                return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            log.error(ErrorLogObject(request, e))
            return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            log.debug(epp_response)
>>>>>>> Switch to rabbitmq for interaction with EPP service

        # Raise an error if this didn't work
        contact_handle = person.contacthandle_set.create(handle=handle,
                                                         provider=provider,
                                                         owner=request.user)
        serializer = ContactHandleSerializer(contact_handle,
                                             context={'request': request})

        return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes((permissions.IsAuthenticated,))
def registrant(request, registry):
    """
    Create or view a registrant for a particular registry.

    :registry: Registry to add this registrant for
    :person_id: Optional person object
    :returns: A contact object

    """

    log.debug("Request for registrant")
    provider = get_object_or_404(DomainProvider.objects.all(), slug=registry)
    if request.method == 'GET':
        try:
            if request.user.is_staff:
                contacts = RegistrantHandle.objects.filter(
                    provider__slug=registry
                )
            else:
                contacts = RegistrantHandle.objects.filter(
                    provider__slug=registry,
                    person__owner=request.user
                )
            serializer = RegistrantHandleSerializer(
                contacts,
                many=True,
                context={"request": request}
            )
            return Response(serializer.data)
        except RegistrantHandle.DoesNotExist:
            raise Http404
    elif request.method == 'POST':
        data = request.data
        log.debug(data)
        person = None
        queryset = PersonalDetail.objects.filter(owner=request.user)
        if request.user.is_staff:
            queryset = PersonalDetail.objects.all()
        if "person" in data:
            person = get_object_or_404(
                queryset,
                pk=data["person"]
            )
        else:
            serializer = PersonalDetailSerializer(data=data)
            if serializer.is_valid():
                person = serializer.save(owner=request.user)
            else:
                raise Exception("Unable to save person.")
        # hacky way to generate a registrant id
        handle = "-".join(["test", "reg", str(person.id), str(RegistrantHandle.objects.count() + 1)])
        try:
            contact_handle = person.registranthandle_set.create(
                handle=handle,
                provider=provider,
                owner=request.user
            )
            street = [person.street1, person.street2, person.street3]
            postal_info = {
                "name": person.first_name + " " + person.surname,
                "org": person.company,
                "type": "int",
                "addr": {
                    "street": street,
                    "city": person.city,
                    "sp": person.state,
                    "pc": person.postcode,
                    "cc": person.country
                }
            }
            contact_info = {
                "command": "createContact",
                "id": handle,
                "voice": person.telephone,
                "fax": person.fax,
                "email": person.email,
                "postalInfo": postal_info
            }
            rpc_client = EppRpcClient(host=rabbit_host)
            contact_info['command'] = 'createContact'
            epp_response = rpc_client.call('epp', registry, json.dumps(contact_info))
            try:
                if int(epp_response["result"]["code"]) >= 2000:
                    log.error(epp_response)
                    return Response(status=status.HTTP_400_BAD_REQUEST)
            except Exception as e:
                log.error(ErrorLogObject(request, e))
                return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                log.debug(epp_response)
        except IntegrityError as e:
            log.error(e)
            return Response(status=status.HTTP_400_BAD_REQUEST)
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

    # Figure out what the tld is and split the submitted domain name into
    # the domain "name" and tld (zone). Also make sure to split away any
    # possible subdomains.
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
    response = requests.post('http://centralnic:3000/createDomain',
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
        log.debug({"result": "Registered domain: %s" % registered_domain.id})
        admin_contact_type = ContactType.objects.get(name='admin')
        tech_contact_type = ContactType.objects.get(name='tech')
        registered_domain.registrant.create(
            registrant=registrant,
            active=True,
            owner=request.user
        )
        registered_domain.contact_handles.create(
            contact_handle=admin,
            active=True,
            contact_type=admin_contact_type,
            owner=request.user
        )
        registered_domain.contact_handles.create(
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


class TopLevelDomainViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomain.objects.all()
    serializer_class = TopLevelDomainSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


class DomainProviderViewSet(viewsets.ModelViewSet):

    queryset = DomainProvider.objects.all()
    serializer_class = DomainProviderSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


class ContactHandleViewSet(viewsets.ModelViewSet):

    serializer_class = ContactHandleSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,
                          permissions.IsAuthenticated)
    queryset = ContactHandle.objects.all()
    filter_backends = (IsPersonFilterBackend,)


class TopLevelDomainProviderViewSet(viewsets.ModelViewSet):

    queryset = TopLevelDomainProvider.objects.all()
    serializer_class = TopLevelDomainProviderSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


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
    permission_classes = (permissions.IsAdminUser,)


class RegisteredDomainViewSet(viewsets.ModelViewSet):

    serializer_class = RegisteredDomainSerializer
    permission_classes = (permissions.DjangoModelPermissionsOrAnonReadOnly,)


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
