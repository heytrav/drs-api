from domain_api.models import Identity
from domain_api.serializers import IdentitySerializer
from django.http import Http404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class IdentityList(APIView):

    """
    List all identities.
    """

    def get(self, request, format=None):
        """
        Handle a GET request

        :request: TODO
        :format: TODO
        :returns: TODO

        """
        identities = Identity.objets.all()
        serializer = IdentitySerializer(identities, many=True)
        return Response(serializer.data)

    def post(self, request, format=None):
        """
        Handle a POST request

        :request: TODO
        :format: TODO
        :returns: TODO

        """
        serializer = IdentitySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)

class IdentityDetail(APIView):

    """
    Display a single identity.
    """
    def get_object(self, pk):
        """
        Return a single object

        :pk: TODO
        :returns: TODO

        """
        try:
            return Identity.objects.get(pk=pk)
        except Identity.DoesNotExist:
            raise Http404

    def get(self, request, pk, format=None):
        """
        Get a single object

        :request: TODO
        :pk: TODO
        :format: TODO
        :returns: TODO

        """
        identity = self.get_object(pk)
        serializer = IdentitySerializer(identity)
        return Response(serializer.data)


