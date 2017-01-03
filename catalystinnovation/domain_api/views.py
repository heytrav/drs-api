import logging
import requests
import json
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


logger = logging.getLogger(__name__)


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
        logger.error("Got response data %s" % available)
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
def registry_contact(request, registry):
    """TODO: Docstring for registry_contact.

    :registry: Registry to add this contact for
    :person_id: Optional person object
    :returns: A contact object

    """

    logger.debug("Request for registry contact")
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
        logger.debug(data)
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

    serializer_class = DomainRegistrantSerializer
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
