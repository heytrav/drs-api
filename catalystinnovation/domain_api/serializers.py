from rest_framework import serializers
from django.contrib.auth.models import User
from domain_api.models import (
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


class PersonalDetailSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for PersonalDetails
    """
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = PersonalDetail
        fields = ('first_name', 'surname', 'middle_name', 'email', 'email2', 'email3',
                  'house_number', 'street1', 'street2', 'street3',
                  'city', 'suburb', 'state', 'postcode', 'country',
                  'created', 'updated', 'owner',)



class UserSerializer(serializers.ModelSerializer):

    """
    Serialize users.
    """

    class Meta:
        model = User
        fields = ('id', 'username')



class ContactTypeSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = ContactType
        fields = ('name', 'description', 'owner')


class TopLevelDomainSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serialize top level domains
    """
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = TopLevelDomain
        fields = ('zone', 'idn_zone', 'description', 'created',
                  'updated', 'owner')


class DomainProviderSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for domain providers.
    """
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = DomainProvider
        fields = ('name', 'description', 'owner')


class RegistrantHandleSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    person = serializers.HyperlinkedRelatedField(
        view_name="domain_api:personaldetail-detail",
        lookup_field="pk",
        read_only=True
    )
    provider=serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = RegistrantHandle
        fields = ('person', 'provider', 'handle', 'created', 'updated', 'owner')


class ContactHandleSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    person = serializers.HyperlinkedRelatedField(
        view_name="domain_api:personaldetail-detail",
        lookup_field="pk",
        read_only=True
    )
    contact_type = serializers.HyperlinkedRelatedField(
        view_name="domain_api:contacttype-detail",
        lookup_field="pk",
        read_only=True
    )
    provider=serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = ContactHandle
        fields = ('person', 'contact_type', 'provider', 'handle',
                  'created', 'updated', 'owner')


class TopLevelDomainProviderSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="pk",
        read_only=True
    )
    zone = serializers.HyperlinkedRelatedField(
        view_name="domain_api:topleveldomain-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = TopLevelDomainProvider
        fields = ( 'zone', 'provider', 'anniversary_notification_period_days',
                  'renewal_period', 'grace_period_days', 'owner')



class DomainSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = Domain
        fields = ('name', 'idn', 'owner')


class RegisteredDomainSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    domain = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domain-detail",
        lookup_field="pk",
        read_only=True
    )
    tld = serializers.HyperlinkedRelatedField(
        view_name="topleveldomain-detail",
        lookup_field="pk",
        read_only=True
    )
    tld_provider = serializers.HyperlinkedRelatedField(
        view_name="topleveldomainprovider-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = RegisteredDomain
        fields = ('domain', 'tld', 'tld_provider', 'active', 'auto_renew',
                  'registration_period', 'anniversary', 'created',
                  'updated', 'owner')


class DomainRegistrantSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    registered_domain = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registereddomain-detail",
        lookup_field="pk",
        read_only=True
    )
    registrant = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registranthandle-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = DomainRegistrant
        fields = ('registered_domain', 'registrant', 'active', 'created',
                  'owner')


class DomainHandlesSerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    registered_domain = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registereddomain-detail",
        lookup_field="pk",
        read_only=True
    )
    contact_handle = serializers.HyperlinkedRelatedField(
        view_name="domain_api:contacthandle-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = DomainHandles
        fields = ('registered_domain', 'contact_handle', 'active',
                  'created', 'owner')

class DomainAvailabilitySerializer(serializers.Serializer):
    domain = serializers.CharField(required=True, allow_blank=False)
    available = serializers.BooleanField(required=True)

class CheckDomainResponseSerializer(serializers.Serializer):
    result = DomainAvailabilitySerializer(many=True)

