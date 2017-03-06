from django.db import models


class PersonalDetail(models.Model):
    """
    Person object in db.
    """

    INT = 'int'
    LOC = 'loc'
    POSTAL_INFO_TYPES =(
        (INT, 'international'),
        (LOC, 'local'),
    )

    first_name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=200)
    email2 = models.CharField(max_length=200, blank=True)
    email3 = models.CharField(max_length=200, blank=True)
    telephone = models.CharField(max_length=200, blank=True)
    fax = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    house_number = models.CharField(max_length=10)
    street1 = models.CharField(max_length=200)
    street2 = models.CharField(max_length=200, blank=True)
    street3 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200)
    suburb = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    postcode = models.CharField(max_length=20)
    # Must be a 2 letter country code.
    country = models.CharField(max_length=2)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    postal_info_type = models.CharField(
        max_length=3,
        choices=POSTAL_INFO_TYPES,
        default=LOC
    )
    disclose_name = models.BooleanField(default=False)
    disclose_company = models.BooleanField(default=False)
    disclose_address = models.BooleanField(default=False)
    disclose_telephone = models.BooleanField(default=False)
    disclose_fax = models.BooleanField(default=False)
    disclose_email = models.BooleanField(default=False)
    default = models.NullBooleanField(null=True)
    project_id = models.ForeignKey('auth.User',
                                   related_name='personal_details',
                                   on_delete=models.CASCADE)

    def __str__(self):
        return self.surname + ', ' + self.first_name

    class Meta:
        unique_together = ('project_id', 'default')




class ContactType(models.Model):
    """
    Types of registry contacts.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()


class TopLevelDomain(models.Model):
    """
    Domain ending model

    Note: for *reasons*, TLDs will be called *zones* inside the application.
    """
    # TLD
    zone = models.CharField(max_length=100, unique=True)
    # Internationalised syntax: xn--*
    idn_zone = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.zone


class DomainProvider(models.Model):
    """
    Registries/rars providing top level domain services
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name


class Registrant(models.Model):
    """
    Registry identifier for a registrant contact.

    This type of contact can only be a registrant for a domain.
    """
    provider = models.ForeignKey(DomainProvider)
    # Id from provider
    registry_id = models.CharField(max_length=200, unique=True)
    project_id = models.ForeignKey('auth.User',
                                   related_name='registrants',
                                   on_delete=models.CASCADE)

    INT = 'int'
    LOC = 'loc'
    POSTAL_INFO_TYPES =(
        (INT, 'international'),
        (LOC, 'local'),
    )
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    telephone = models.CharField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    house_number = models.CharField(max_length=10, null=True, blank=True)
    street1 = models.CharField(max_length=200, null=True)
    street2 = models.CharField(max_length=200, null=True, blank=True)
    street3 = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True)
    suburb = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(max_length=200, null=True, blank=True)
    status = models.CharField(max_length=200, null=True)
    postcode = models.CharField(max_length=20, null=True)
    # Must be a 2 letter country code.
    country = models.CharField(max_length=2, null=True)
    postal_info_type = models.CharField(
        max_length=3,
        choices=POSTAL_INFO_TYPES,
        default=LOC
    )
    authcode = models.CharField(max_length=100, null=True, blank=True)
    roid = models.CharField(max_length=100, null=True, blank=True)
    disclose_name = models.BooleanField(default=False)
    disclose_company = models.BooleanField(default=False)
    disclose_address = models.BooleanField(default=False)
    disclose_telephone = models.BooleanField(default=False)
    disclose_fax = models.BooleanField(default=False)
    disclose_email = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    default = models.NullBooleanField(null=True)

    class Meta:
        unique_together = ('project_id', 'default')

class Contact(models.Model):
    """
    Registry identifier for a contact registry_id.
    """
    INT = 'int'
    LOC = 'loc'
    POSTAL_INFO_TYPES =(
        (INT, 'international'),
        (LOC, 'local'),
    )
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    telephone = models.CharField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    house_number = models.CharField(max_length=10, null=True, blank=True)
    street1 = models.CharField(max_length=200, null=True)
    street2 = models.CharField(max_length=200, null=True, blank=True)
    street3 = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=200, null=True)
    suburb = models.CharField(max_length=200, null=True, blank=True)
    state = models.CharField(max_length=200, null=True, blank=True)
    postcode = models.CharField(max_length=20, null=True)
    # Must be a 2 letter country code.
    country = models.CharField(max_length=2, null=True)
    postal_info_type = models.CharField(
        max_length=3,
        choices=POSTAL_INFO_TYPES,
        default=LOC
    )
    authcode = models.CharField(max_length=100, null=True, blank=True)
    roid = models.CharField(max_length=100, null=True, blank=True)
    disclose_name = models.BooleanField(default=False)
    disclose_company = models.BooleanField(default=False)
    disclose_address = models.BooleanField(default=False)
    disclose_telephone = models.BooleanField(default=False)
    disclose_fax = models.BooleanField(default=False)
    disclose_email = models.BooleanField(default=False)
    provider = models.ForeignKey(DomainProvider)
    status = models.CharField(max_length=200, null=True)
    # Id from provider
    registry_id = models.CharField(max_length=200, unique=True)
    project_id = models.ForeignKey('auth.User',
                                   related_name='contacts',
                                   on_delete=models.CASCADE)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class TopLevelDomainProvider(models.Model):
    """
    Match a provider with a TLD.
    """

    zone = models.ForeignKey(TopLevelDomain)
    provider = models.ForeignKey(DomainProvider)
    anniversary_notification_period_days = models.IntegerField()
    renewal_period = models.IntegerField(default=30)
    grace_period_days = models.IntegerField(default=30)

    def __str__(self):
        return self.zone.zone + " " + self.provider.name


class Domain(models.Model):
    """
    Represent a domain.
    """
    # The part of a domain name before the tld
    name = models.CharField(max_length=200, unique=True)
    # punyencoded version of the name field. For ascii domains this will
    # be identical to name.
    idn = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class RegisteredDomain(models.Model):
    """
    Represent a registered domain name.

    A registered domain is a combined Domain + TopLevelDomainProvider
    object as it may be possible to register the same tld from multiple sources.
    Providers may have their own unique rules around renewal period and notifications.
    """
    domain = models.ForeignKey(Domain)
    # Needed to enforce unique constraint
    tld = models.ForeignKey(TopLevelDomain)
    tld_provider = models.ForeignKey(TopLevelDomainProvider)
    # Need to see if this can be constrained to be just a registrant.
    active = models.NullBooleanField(null=True)
    auto_renew = models.BooleanField(default=True)
    registration_period = models.IntegerField()
    # This will need to be a meta field that is calculated based on the
    # registration period and whatever the notification buffer is for a
    # provider. The aim is to notify a customer ahead of time that their domain
    # is about to renew/expire.
    anniversary = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('domain', 'tld', 'active')

    def __str__(self):
        """
        Represent a registered domain (i.e. name.tld).
        """
        return self.domain.name + "." + self.tld_provider.zone.zone


class DomainRegistrant(models.Model):
    """
    Registrant associated with a domain. A domain can typically have only one.
    """
    registered_domain = models.ForeignKey(RegisteredDomain,
                                          related_name="registrant")
    registrant = models.ForeignKey(Registrant)
    active = models.NullBooleanField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('registered_domain', 'registrant', 'active')


class DomainContact(models.Model):
    """
    Contact associated with a domain. A domain can have several contact registry_ids
    (depending on the registry).
    """
    registered_domain = models.ForeignKey(RegisteredDomain,
                                          related_name='contacts')
    contact = models.ForeignKey(Contact)
    contact_type = models.ForeignKey(ContactType)
    active = models.NullBooleanField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('registered_domain', 'contact_type', 'contact', 'active')

class NameserverHost(models.Model):

    """
    Nameserver

    i.e. ns1.something.com
    """
    host = models.CharField(max_length=255, unique=True)
    domain_nameserver = models.ManyToManyField(RegisteredDomain)
    default = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)


class IpAddress(models.Model):

    """
    IP address.
    """

    V4 = 'v4'
    V6 = 'v6'
    IP_ADDRESS_TYPES = (
        (V4, 'ipv4'),
        (V6, 'ipv6'),
    )
    address = models.CharField(max_length=255, unique=True)
    address_type = models.CharField(
        max_length=2,
        choices=IP_ADDRESS_TYPES,
        default=V4
    )
    nameserver_host = models.ManyToManyField(NameserverHost)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    project_id = models.ForeignKey('auth.User',
                                   related_name='ip_addresses',
                                   on_delete=models.CASCADE)
