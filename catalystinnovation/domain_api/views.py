from domain_api.models import Identity
from django.contrib.auth.models import User
from domain_api.serializers import IdentitySerializer, UserSerializer
from domain_api.permissions import IsOwnerOrReadOnly
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, mixins, generics, permissions
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.reverse import reverse

@api_view(['GET'])
def api_root(request, format=None):
    """
    Root of the API.

    :request: TODO
    :format: TODO
    :returns: TODO

    """
    return Response({
        'users': reverse('user-list', request=request, format=format),
        'identites': reverse('identity-list', request=request, format=format),
    })


class IdentityList(generics.ListCreateAPIView):

    """
    List all identities.
    """
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly,)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class IdentityDetail(generics.RetrieveUpdateDestroyAPIView):

    """
    Display a single identity.
    """
    queryset = Identity.objects.all()
    serializer_class = IdentitySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,
                          IsOwnerOrReadOnly)


class UserList(generics.ListAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetail(generics.RetrieveAPIView):

    queryset = User.objects.all()
    serialzer_class = UserSerializer
