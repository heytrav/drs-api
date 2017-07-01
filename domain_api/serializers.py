import logging
from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from domain_api.models import (
    AccountDetail,
    TopLevelDomain,
    ContactType,
    DomainProvider,
    Registrant,
    Contact,
    TopLevelDomainProvider,
    RegisteredDomain,
    DomainContact,
    DefaultAccountTemplate,
    DefaultAccountContact,
    Nameserver,
)
import uuid
from . import schemas
import jsonschema
log = logging.getLogger(__name__)

UserModel = get_user_model()


class NonDiscloseField(serializers.JSONField):
    def to_internal_value(self, data):
        """
        Validate the representation of the non_disclose field

        :data: list of disclose data
        :returns: serialized data

        """
        if data is None:
            data = ["name",
                    "address",
                    "company",
                    "telephone",
                    "fax",
                    "email"]
        try:
            jsonschema.validate(data, schemas.non_disclose)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(detail=e.message)
        return super().to_internal_value(data)

    def to_representation(self, obj):
        if obj is None:
            obj = []
        return obj


class StreetField(serializers.JSONField):
    def to_internal_value(self, data):
        """
        Validate the representation of the non_disclose field

        :data: list of disclose data
        :returns: serialized data

        """
        try:
            jsonschema.validate(data, schemas.street)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(detail=e.message)
        return super().to_internal_value(data)

    def to_representation(self, obj):
        return obj


class IpAddrField(serializers.JSONField):
    def to_internal_value(self, data):
        """
        Validate the representation of the ip address field

        :data: list of disclose data
        :returns: serialized data

        """
        try:
            jsonschema.validate(data, schemas.ip_addr)
        except jsonschema.exceptions.ValidationError as e:
            raise ValidationError(detail=e.message)
        return super().to_internal_value(data)

    def to_representation(self, obj):
        return obj


class AccountDetailSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for AccountDetails
    """
    user = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:account-detail",
        lookup_field="pk"
    )
    def default_non_disclose():
        """
        Set default values for non_disclose.
        """
        return ["name", "address", "company", "telephone", "fax", "email"]

    def default_street_name():
        """
        Set default street name
        :returns: list with default street.

        """
        return ["Street Name"]

    non_disclose = NonDiscloseField(default=default_non_disclose)
    street = StreetField(default=default_street_name)

    class Meta:
        model = AccountDetail
        fields = ('url', 'first_name', 'surname', 'email',
                  'telephone', 'fax', 'company', 'street', 'city',
                  'state', 'postcode', 'country', 'postal_info_type',
                  'created', 'updated', 'user', 'default_registrant',
                  'non_disclose',)


class UserSerializer(serializers.ModelSerializer):

    """
    Serialize users.
    """
    password = serializers.CharField(write_only=True)

    def create(self, validated_data):
        """
        Override create method to create this user using specific User
        related methods.

        :validated_data: data validated for serializer
        :returns: User object

        """
        user = UserModel.objects.create(
            username=validated_data["username"]
        )
        user.set_password(validated_data["password"])
        if "email" in validated_data:
            user.email = validated_data["email"]
        if "first_name" in validated_data:
            user.first_name = validated_data["first_name"]
        if "last_name" in validated_data:
            user.last_name = validated_data["last_name"]

        user.save()
        user.groups.add(Group.objects.get(name="customer"))
        return user

    class Meta:
        model = UserModel
        fields = ('id', 'username', 'password', 'first_name', 'last_name')


class ContactTypeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:contacttype-detail",
        lookup_field="name"
    )

    class Meta:
        model = ContactType
        fields = ('name', 'description', 'url')


class TopLevelDomainSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serialize top level domains
    """
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:topleveldomain-detail",
        lookup_field="slug"
    )

    class Meta:
        model = TopLevelDomain
        fields = ('zone', 'tld', 'description', 'created',
                  'updated', 'url', 'slug',)
        read_only_fields = ('slug',)


class DomainProviderSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for domain providers.
    """
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="slug"
    )

    class Meta:
        model = DomainProvider
        fields = ('name', 'description', 'slug', 'url', 'active',)


class RegistrantSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:registrant-detail",
        lookup_field="registry_id",
    )
    provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="slug",
        read_only=True
    )
    user = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = Registrant
        fields = ('url', 'provider', 'registry_id', 'name',
                  'email', 'telephone', 'fax', 'company',
                  'street', 'city', 'state',
                  'postcode', 'country', 'postal_info_type', 'non_disclose',
                   'created', 'updated', 'status', 'user',)


class ContactSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:contact-detail",
        lookup_field="registry_id",
        read_only=True
    )
    provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="slug",
        read_only=True
    )
    user = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = Contact
        fields = ('url', 'provider', 'registry_id', 'name',
                  'email', 'telephone', 'fax', 'company',
                  'street', 'city', 'state',
                  'postcode', 'country', 'postal_info_type',
                  'non_disclose', 'created', 'updated',
                  'status', 'user',)


class TopLevelDomainProviderSerializer(serializers.HyperlinkedModelSerializer):
    provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="slug",
        read_only=True
    )
    zone = serializers.HyperlinkedRelatedField(
        view_name="domain_api:topleveldomain-detail",
        lookup_field="slug",
        read_only=True
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:topleveldomainprovider-detail",
        lookup_field="pk"
    )

    class Meta:
        model = TopLevelDomainProvider
        fields = ('zone', 'provider', 'expiration_notification_period_days',
                  'active',
                  'renewal_period', 'grace_period_days', 'url')


class RegisteredDomainSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:registereddomain-detail",
        lookup_field="pk"
    )
    tld = serializers.SlugRelatedField(many=False,
                                       read_only=True,
                                       slug_field='zone')
    tld_provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:topleveldomainprovider-detail",
        lookup_field="pk",
        read_only=True
    )
    registrant = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registrant-detail",
        lookup_field="registry_id",
        read_only=True
    )
    contacts = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domaincontact-detail",
        many=True,
        read_only=True
    )

    class Meta:
        model = RegisteredDomain
        fields = ('domain', 'name', 'tld', 'tld_provider', 'active', 'auto_renew',
                  'status', 'nameservers',
                  'registration_period', 'expiration', 'created',
                  'updated', 'registrant', 'contacts', 'url',)


class DomainContactSerializer(serializers.HyperlinkedModelSerializer):
    registered_domain = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registereddomain-detail",
        lookup_field="fqdn",
        read_only=True
    )
    contact = serializers.HyperlinkedRelatedField(
        view_name="domain_api:contact-detail",
        lookup_field="registry_id",
        read_only=True
    )
    contact_type = serializers.HyperlinkedRelatedField(
        view_name="domain_api:contacttype-detail",
        lookup_field="name",
        read_only=True
    )

    class Meta:
        model = DomainContact
        fields = ('registered_domain', 'contact_type', 'contact', 'active',
                  'created')


class DefaultAccountTemplateSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:defaultaccounttemplate-detail",
        lookup_field="pk"
    )

    class Meta:
        model = DefaultAccountTemplate
        fields = ('url', 'account_template', 'provider', 'user')


class DefaultAccountContactSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:defaultaccountcontact-detail",
        lookup_field="pk"
    )

    class Meta:
        model = DefaultAccountContact
        fields = ('url', 'user', 'account_template', 'contact_type', 'provider',
                  'mandatory')


class DomainAvailabilitySerializer(serializers.Serializer):
    domain = serializers.CharField(required=True, allow_blank=False)
    available = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False)


class HostAvailabilitySerializer(serializers.Serializer):
    host = serializers.CharField(required=True, allow_blank=False)
    available = serializers.BooleanField(required=True)
    reason = serializers.CharField(required=False)


class CheckDomainResponseSerializer(serializers.Serializer):
    result = DomainAvailabilitySerializer(many=True)


class PrivateInfoDomainSerializer(serializers.ModelSerializer):
    domain = serializers.SerializerMethodField("get_fqdn")
    registrant = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()
    nameservers = serializers.JSONField()
    provider = serializers.SerializerMethodField()

    class Meta:
        model = RegisteredDomain
        fields = ('domain', 'contacts', 'registrant', 'nameservers',
                  'provider', 'authcode', 'created', 'expiration')
        read_only_fields = ('fqdn', 'expiration', 'created', 'authcode', 'status')

    def get_fqdn(self, obj):
        """
        Return the fqdn

        :obj: TODO
        :returns: TODO

        """
        fqdn = str(uuid.uuid4())[:8]
        try:
            fqdn = obj.fqdn
        except Exception as e:
            log.error(e.message)
        return obj.fqdn

    def get_registrant(self, obj):
        return obj.registrant.registry_id

    def get_contacts(self, obj):
        active_contacts = obj.contacts.filter(active=True)
        return [{i.contact_type.name: i.contact.registry_id}
                for i in active_contacts]

    def get_provider(self, obj):
        """
        Return provider for domain

        :obj: RegisteredDomain object
        :returns: str abbreviation for registry

        """
        return obj.tld_provider.provider.slug


class AdminInfoDomainSerializer(PrivateInfoDomainSerializer):
    class Meta:
        model = RegisteredDomain
        fields = ('domain', 'contacts', 'registrant', 'roid',
                  'status', 'authcode',
                  'created', 'expiration')
        read_only_fields = ('roid', 'expiration', 'created', 'authcode',
                            'status')


class NameserverSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serialize nameserver objects.
    """
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:nameserver-detail",
        lookup_field="pk"
    )

    class Meta:
        model = Nameserver
        fields = ('url', 'idn_host', 'host', 'addr',
                  'created', 'updated')

class AdminNameserverSerializer(NameserverSerializer):

    """
    Serialize nameserver objects.
    """

    tld_provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:topleveldomainprovider-detail",
        lookup_field="pk",
        read_only=True,
    )
    user = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = Nameserver
        fields = ('url', 'idn_host', 'host', 'addr',
                  'tld_provider', 'default',
                  'created', 'updated', 'status', 'roid', 'user')


class InfoHostSerializer(serializers.ModelSerializer):

    addr = IpAddrField()

    class Meta:
        model = Nameserver
        fields = ('host', 'idn_host', 'addr')

class AdminInfoHostSerializer(InfoHostSerializer):

    class Meta:
        model = Nameserver
        fields = ('host', 'idn_host', 'tld_provider', 'default', 'addr',
                  'created', 'updated', 'status', 'roid', 'user')
        read_only_fields = ('user', 'tld_provider')


class QueryInfoHostSerializer(serializers.Serializer):
    host = serializers.CharField(required=True, allow_blank=False)
    addr = IpAddrField()


class PrivateInfoContactSerializer(serializers.ModelSerializer):

    provider = serializers.SerializerMethodField()

    class Meta:
        model = Contact
        fields = ('registry_id', 'name', 'email', 'company', 'street',
                  'city', 'telephone', 'fax',
                  'state', 'country', 'postcode',
                  'postal_info_type', 'non_disclose',
                  'authcode', 'provider',)

    def get_provider(self, obj):
        """
        Return the provider for this contact

        :obj: Contact object
        :returns: str registry slug

        """
        return obj.provider.slug


class AdminInfoContactSerializer(PrivateInfoContactSerializer):

    class Meta:
        model = Contact
        fields = ('registry_id', 'name', 'email', 'company', 'street',
                  'city', 'telephone', 'fax',
                  'state', 'country', 'postcode',
                  'postal_info_type', 'non_disclose',
                  'status', 'authcode', 'roid', 'user', 'provider',)


class PrivateInfoRegistrantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Registrant
        fields = ('registry_id', 'name', 'email', 'company', 'street',
                  'city', 'telephone', 'fax',
                  'state', 'country', 'postcode',
                  'postal_info_type', 'non_disclose',
                  'authcode',)


class AdminInfoRegistrantSerializer(serializers.ModelSerializer):

    class Meta:
        model = Registrant
        fields = ('registry_id', 'name', 'email', 'company', 'street',

                  'city', 'telephone', 'fax',
                  'state', 'country', 'postcode',
                  'postal_info_type', 'non_disclose',
                  'status', 'authcode', 'roid', 'user',)
