from rest_framework import serializers
from domain_api.models import Identity, PersonalDetail

class IdentitySerializer(serializers.ModelSerializer):
    class Meta:
        model = Identity
        fields = ('id', 'first_name', 'surname', 'middle_name', 'username',)

