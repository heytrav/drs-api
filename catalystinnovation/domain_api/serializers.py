from rest_framework import serializers
from django.contrib.auth.models import User
from domain_api.models import (
    Identity,
    PersonalDetail,
    TopLevelDomain,
    ContactType,
    DomainProvider,
    RegistrantHandle,
    ContactHandle,
    TopLevelDomainProvider,
    Domain,
    RegisteredDomain,
    DomainRegistrant,
    DomainHandles
)


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


class PersonalDetailSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for PersonalDetails
    """
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = PersonalDetail
        fields = ('identity', 'email', 'email2', 'email3',
                  'house_number', 'street1', 'street2', 'street3',
                  'city', 'suburb', 'state', 'postcode', 'country',
                  'created', 'updated', 'owner')


class ContactTypeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = ContactType
        fields = ('name', 'description', 'owner')


class TopLevelDomainSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serialize top level domains
    """
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = TopLevelDomain
        fields = ('zone', 'idn_zone', 'description', 'created',
                  'updated', 'owner')


class DomainProviderSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for domain providers.
    """
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = DomainProvider
        fields = ('name', 'description', 'owner')


class RegistrantHandleSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = RegistrantHandle
        fields = ('person', 'provider', 'handle', 'created', 'updated', 'owner')


class ContactHandleSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = ContactHandle
        fields = ('person', 'contact_type', 'provider', 'handle',
                  'created', 'updated', 'owner')


class TopLevelDomainProviderSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = TopLevelDomainProvider
        fields = ('zone', 'provider', 'anniversary_notification_period_days',
                  'renewal_period', 'grace_period_days', 'owner')


class DomainSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = Domain
        fields = ('name', 'idn', 'owner')


class RegisteredDomainSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = RegisteredDomain
        fields = ('domain', 'tld', 'tld_provider', 'active', 'auto_renew',
                  'registration_period', 'anniversary', 'created',
                  'updated', 'owner')


class DomainRegistrantSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = DomainRegistrant
        fields = ('registered_domain', 'registrant', 'active', 'created',
                  'owner')


class DomainHandlesSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')

    class Meta:
        model = DomainHandles
        fields = ('registered_domain', 'contact_handle', 'active',
                  'created', 'owner')
