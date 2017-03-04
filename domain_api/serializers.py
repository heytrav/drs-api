from rest_framework import serializers
from django.contrib.auth.models import User
from domain_api.models import (
    PersonalDetail,
    TopLevelDomain,
    ContactType,
    DomainProvider,
    Registrant,
    Contact,
    TopLevelDomainProvider,
    Domain,
    RegisteredDomain,
    DomainRegistrant,
    DomainContact
)


class PersonalDetailSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for PersonalDetails
    """
    project_id = serializers.HyperlinkedRelatedField(
        view_name="domain_api:user-detail",
        lookup_field="pk",
        read_only=True
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:personal-detail",
        lookup_field="pk"
    )

    class Meta:
        model = PersonalDetail
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

    class Meta:
        model = User
        fields = ('id', 'username')


class ContactTypeSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:contacttype-detail",
        lookup_field="pk"
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
        lookup_field="pk"
    )

    class Meta:
        model = TopLevelDomain
        fields = ('zone', 'idn_zone', 'description', 'created',
                  'updated', 'url')


class DomainProviderSerializer(serializers.HyperlinkedModelSerializer):

    """
    Serializer for domain providers.
    """
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="pk"
    )

    class Meta:
        model = DomainProvider
        fields = ('name', 'description', 'slug', 'url')


class RegistrantSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:registrant-detail",
        lookup_field="pk"
    )
    provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="pk",
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
        lookup_field="pk",
        read_only=True
    )
    provider = serializers.HyperlinkedRelatedField(
        view_name="domain_api:domainprovider-detail",
        lookup_field="pk",
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
        lookup_field="pk",
        read_only=True
    )
    zone = serializers.HyperlinkedRelatedField(
        view_name="domain_api:topleveldomain-detail",
        lookup_field="pk",
        read_only=True
    )
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:topleveldomainprovider-detail",
        lookup_field="pk"
    )

    class Meta:
        model = TopLevelDomainProvider
        fields = ('zone', 'provider', 'anniversary_notification_period_days',
                  'renewal_period', 'grace_period_days', 'url')


class DomainSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name="domain_api:domain-detail",
        lookup_field="pk"
    )

    class Meta:
        model = Domain
        fields = ('name', 'idn', 'url')


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
                  'registration_period', 'anniversary', 'created',
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
        lookup_field="pk",
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
        lookup_field="pk",
        read_only=True
    )
    contact_type = serializers.HyperlinkedRelatedField(
        view_name="domain_api:contacttype-detail",
        lookup_field="pk",
        read_only=True
    )

    class Meta:
        model = DomainContact
        fields = ('registered_domain', 'contact_type', 'contact', 'active',
                  'created')


class DomainAvailabilitySerializer(serializers.Serializer):
    domain = serializers.CharField(required=True, allow_blank=False)
    available = serializers.BooleanField(required=True)


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


class InfoDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(required=True, allow_blank=False)
    contacts = HandleSetSerializer()
    registrant = serializers.CharField(required=True, allow_blank=False)
    roid = serializers.CharField()
    ns = NsHostObjectListSerializer(required=False)
    status = serializers.CharField(required=False, allow_blank=True)
    authcode = serializers.CharField(required=False, allow_blank=True)
    roid = serializers.CharField(required=False, allow_blank=True)
    created = serializers.DateTimeField(required=False)
    anniversary = serializers.DateTimeField(required=False)


class InfoDomainListSerializer(serializers.ListField):

    """
    Serialise a set of domains into respective info description.
    """
    child = InfoDomainSerializer()


class InfoContactSerializer(serializers.Serializer):

    registry_id = serializers.CharField(required=False, allow_blank=True)
    name = serializers.CharField(required=False, allow_blank=True)
    email = serializers.CharField(required=False, allow_blank=True)
    company = serializers.CharField(required=False, allow_blank=True)
    city = serializers.CharField(required=False, allow_blank=True)
    telephone = serializers.CharField(required=False, allow_blank=True)
    fax = serializers.CharField(required=False, allow_blank=True)
    house_number = serializers.CharField(required=False, allow_blank=True)
    street1 = serializers.CharField(required=False, allow_blank=True)
    street2 = serializers.CharField(required=False, allow_blank=True)
    street3 = serializers.CharField(required=False, allow_blank=True)
    state = serializers.CharField(required=False, allow_blank=True)
    country = serializers.CharField(required=False, allow_blank=True)
    postcode = serializers.CharField(required=False, allow_blank=True)
    postal_info_type = serializers.CharField(required=False, allow_blank=True)
    disclose_name = serializers.BooleanField()
    disclose_company = serializers.BooleanField()
    disclose_telephone = serializers.BooleanField()
    disclose_fax = serializers.BooleanField()
    disclose_email = serializers.BooleanField()
    disclose_address = serializers.BooleanField()
    status = serializers.CharField(required=False)
    authcode = serializers.CharField(required=False)


class ContactDomainSerializer(serializers.Serializer):
    domain = serializers.CharField(required=True)
    created = serializers.DateTimeField(required=True)
    anniversary = serializers.DateTimeField(required=True)


class ContactDomainSetSerializer(serializers.ListField):
    child = ContactDomainSerializer()


class ContactDomainResultSerializer(serializers.Serializer):
    result = ContactDomainSetSerializer(required=True)
