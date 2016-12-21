from domain_api.models import Identity
from domain_api.serializers import IdentitySerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, generics

class IdentityList(generics.ListCreateAPIView):

    """
    List all identities.
    """
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer

class IdentityDetail(generics.RetrieveUpdateDestroyAPIView):

    """
    Display a single identity.
    """
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer
