from rest_framework import serializers
from django.contrib.auth.models import User
from domain_api.models import Identity


class UserSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serialize users.
    """
    identities = serializers.HyperlinkedRelatedField(
        many=True,
        view_name="identity-detail",
        read_only=True
    )

    class Meta:
        model = User
        fields = ('id', 'username', 'identities')


class IdentitySerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Identity
        fields = ('id', 'first_name', 'surname',
                  'middle_name', 'username', 'owner',)
