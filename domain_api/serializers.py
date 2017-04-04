from rest_framework import serializers
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
    Domain,
    RegisteredDomain,
    DomainRegistrant,
    DomainContact,
    DefaultAccountTemplate,
    NameserverHost,
)

UserModel = get_user_model()


class AccountDetailSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for AccountDetails
    """
    project_id = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:account-detail",
        lookup_field="pk"
    )

    class Meta:
        model = AccountDetail
        fields = ('url', 'first_name', 'surname', 'middle_name', 'email',
                  'email2', 'email3', 'telephone', 'fax', 'company',
                  'house_number', 'street1', 'street2', 'street3', 'city',
                  'suburb', 'state', 'postcode', 'country', 'postal_info_type',
                  'disclose_name', 'disclose_company', 'disclose_address',
                  'disclose_telephone', 'disclose_fax', 'disclose_email',
                  'created', 'updated', 'project_id',)


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
                  'updated', 'url',)


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
        fields = ('name', 'description', 'slug', 'url',)


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
    project_id = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = Registrant
        fields = ('url', 'provider', 'registry_id', 'name',
                  'email', 'telephone', 'fax', 'company', 'house_number',
                  'street1', 'street2', 'street3', 'city', 'suburb', 'state',
                  'postcode', 'country', 'postal_info_type', 'disclose_name',
                  'disclose_company', 'disclose_address', 'disclose_telephone',
                  'disclose_fax', 'disclose_email', 'created', 'updated',
                  'project_id',)


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
    project_id = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = Contact
        fields = ('url', 'provider', 'registry_id', 'name',
                  'email', 'telephone', 'fax', 'company', 'house_number',
                  'street1', 'street2', 'street3', 'city', 'suburb', 'state',
                  'postcode', 'country', 'postal_info_type', 'disclose_name',
                  'disclose_company', 'disclose_address', 'disclose_telephone',
                  'disclose_fax', 'disclose_email', 'created', 'updated',
                  'project_id',)


class TopLevelDomainProviderSerializer(serializers.HyperlinkedModelSerializer):
    provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="slug",
        read_only=True
    )
    zone = serializers.HyperlinkedRelatedField(
        view_name="domain_api:topleveldomain-detail",
        lookup_field="zone",
        read_only=True
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:topleveldomainprovider-detail",
        lookup_field="pk"
    )

    class Meta:
        model = TopLevelDomainProvider
        fields = ('zone', 'provider', 'expiration_notification_period_days',
                  'renewal_period', 'grace_period_days', 'url')


class DomainSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:domain-detail",
        lookup_field="name"
    )

    class Meta:
        model = Domain
        fields = ('domain', 'name', 'url')


class RegisteredDomainSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:registereddomain-detail",
        lookup_field="pk"
    )
    domain = serializers.SlugRelatedField(many=False,
                                          read_only=True,
                                          slug_field='name')
    tld = serializers.SlugRelatedField(many=False,
                                       read_only=True,
                                       slug_field='zone')
    tld_provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:topleveldomainprovider-detail",
        lookup_field="pk",
        read_only=True
    )
    registrant = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainregistrant-detail",
        many=True,
        read_only=True
    )
    contacts = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domaincontact-detail",
        many=True,
        read_only=True
    )

    class Meta:
        model = RegisteredDomain
        fields = ('domain', 'tld', 'tld_provider', 'active', 'auto_renew',
                  'registration_period', 'expiration', 'created',
                  'updated', 'registrant', 'contacts', 'url')


class DomainRegistrantSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:domainregistrant-detail",
        lookup_field="pk"
    )
    registered_domain = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registereddomain-detail",
        lookup_field="pk",
        read_only=True
    )
    registrant = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registrant-detail",
        lookup_field="registry_id",
        read_only=True
    )

    class Meta:
        model = DomainRegistrant
        fields = ('registered_domain', 'registrant', 'active', 'created', 'url')


class DomainContactSerializer(serializers.HyperlinkedModelSerializer):
    registered_domain = serializers.HyperlinkedRelatedField(
        view_name="domain_api:registereddomain-detail",
        lookup_field="pk",
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
    provider = serializers.SlugRelatedField(slug_field='slug', read_only=True)

    class Meta:
        model = DefaultAccountTemplate
        fields = ('id', 'account_template', 'provider', 'project_id')
        read_only_fields = ('id', 'project_id',)


class DefaultAccountContactSerializer(serializers.ModelSerializer):
    provider = serializers.SlugRelatedField(slug_field='slug', read_only=True)
    contact_type = serializers.SlugRelatedField(slug_field='name',
                                                read_only=True)

    class Meta:
        model = DefaultAccountTemplate
        fields = ('project_id', 'account_template', 'contact_type', 'provider',
                  'mandatory')
        read_only_fields = ('project_id',)


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


class HandleTypeSerializer(serializers.Serializer):
    contact = serializers.CharField(required=True, allow_blank=False)
    contact_type = serializers.CharField(required=True, allow_blank=False)


class NsHostObjectListSerializer(serializers.ListField):
    child = serializers.CharField()


class HandleSetSerializer(serializers.ListField):
    admin = serializers.CharField(required=False)
    tech = serializers.CharField(required=False)
    billing = serializers.CharField(required=False)
    zone = serializers.CharField(required=False)

class PrivateInfoHostSerializer(serializers.ModelSerializer):

    host = serializers.SerializerMethodField()
    idn_host = serializers.SerializerMethodField()
    addr = serializers.SerializerMethodField()
    roid = serializers.CharField(required=False)

    class Meta:
        model = NameserverHost
        fields = ('host', 'idn_host', 'addr', 'created', 'updated',
                  'status', 'roid', 'project_id')
        read_only_fields = ('status', 'project_id', 'created', 'updated',
                            'roid')

    def get_host(self, obj):
        """
        Return the host

        :obj: object
        :returns: str host
        """
        return obj.nameserver.host

    def get_idn_host(self, obj):
        """
        Return the idn host name

        :obj: object
        :returns: str internationalised host
        """
        return obj.nameserver.idn_host

    def get_addr(self, obj):
        """
        Return the set of addresses

        :obj: TODO
        :returns: TODO
        """
        ipaddress_set = obj.ipaddress_set.all()
        return [{"ip": i.ip, "addr_type": i.address_type} for i in ipaddress_set]


class PrivateInfoDomainSerializer(serializers.ModelSerializer):
    domain = serializers.SerializerMethodField('get_fqdn')
    registrant = serializers.SerializerMethodField()
    contacts = serializers.SerializerMethodField()

    class Meta:
        model = RegisteredDomain
        fields = ('domain', 'contacts', 'registrant', 'roid', 'ns',
                  'status', 'authcode', 'created', 'expiration')
        read_only_fields = ('roid', 'expiration', 'created', 'authcode',
                            'status')

    def get_registrant(self, obj):
        return obj.registrant.filter(active=True).first().registrant.registry_id

    def get_fqdn(self, obj):
        return ".".join([obj.domain.domain, obj.tld.tld])

    def get_contacts(self, obj):
        active_contacts = obj.contacts.filter(active=True)
        return [{i.contact_type.name: i.contact.registry_id} for i in active_contacts]


class OwnerInfoDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(required=True, allow_blank=False)
    contacts = HandleSetSerializer()
    registrant = serializers.CharField(required=True, allow_blank=False)
    roid = serializers.CharField()
    ns = NsHostObjectListSerializer(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    authcode = serializers.CharField(required=False, allow_blank=True)
    roid = serializers.CharField(required=False, allow_blank=True)
    created = serializers.DateTimeField(required=False)
    expiration = serializers.DateTimeField(required=False)


class InfoDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(required=True, allow_blank=False)
    contacts = HandleSetSerializer()
    registrant = serializers.CharField(required=True, allow_blank=False)
    roid = serializers.CharField(required=False)
    ns = NsHostObjectListSerializer(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    created = serializers.DateTimeField(required=False)
    expiration = serializers.DateTimeField(required=False)


class IpAddressSerializer(serializers.Serializer):
    ip = serializers.CharField(required=True)
    addr_type = serializers.CharField(required=False)


class AddressSetField(serializers.ListField):
    child = IpAddressSerializer()


class InfoHostSerializer(serializers.Serializer):
    host = serializers.CharField(required=True, allow_blank=False)
    addr = AddressSetField(min_length=1)


class InfoDomainListSerializer(serializers.ListField):

    """
    Serialise a set of domains into respective info description.
    """
    child = InfoDomainSerializer()


class PrivateInfoContactSerializer(serializers.ModelSerializer):

    class Meta:
        model = Contact
        fields = ('registry_id', 'name', 'email', 'company', 'street1',
                  'street2', 'street3', 'city', 'telephone', 'fax',
                  'house_number', 'state', 'country', 'postcode',
                  'postal_info_type', 'disclose_name', 'disclose_company',
                  'disclose_telephone', 'disclose_email', 'disclose_address',
                  'status', 'authcode', 'disclose_fax',)


class InfoContactSerializer(serializers.Serializer):

    registry_id = serializers.CharField()
    name = serializers.CharField(required=False)
    email = serializers.CharField(required=False)
    company = serializers.CharField(required=False)
    house_number = serializers.CharField(required=False)
    street1 = serializers.CharField(required=False)
    street2 = serializers.CharField(required=False)
    street3 = serializers.CharField(required=False)
    city = serializers.CharField(required=False)
    state = serializers.CharField(required=False)
    country = serializers.CharField(required=False)
    postcode = serializers.CharField(required=False)
    postal_info_type = serializers.CharField(required=False)

    class Meta:
        model = Contact
        fields = ('registry_id', 'name', 'email', 'company', 'street1',
                  'street2', 'street3', 'city', 'telephone', 'fax',
                  'house_number', 'state', 'country', 'postcode',
                  'postal_info_type',)
        read_only_fields = ('registry_id', 'postal_info_type')


class ContactDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(required=True)
    created = serializers.DateTimeField(required=True)
    expiration = serializers.DateTimeField(required=True)


class ContactDomainSetSerializer(serializers.ListField):
    child = ContactDomainSerializer()


class ContactDomainResultSerializer(serializers.Serializer):
    result = ContactDomainSetSerializer(required=True)
