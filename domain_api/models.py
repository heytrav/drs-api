from django.db import models
from django_mysql.models import JSONField
import idna
import re
import uuid


class AccountDetail(models.Model):
    """
    Person object in db.
    """

    INT = 'int'
    LOC = 'loc'
    POSTAL_INFO_TYPES = (
        (INT, 'international'),
        (LOC, 'local'),
    )

    first_name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    telephone = models.CharField(max_length=200, blank=True)
    fax = models.CharField(max_length=200, blank=True)
    company = models.CharField(max_length=200, blank=True)
    street = JSONField(default=None, null=True)
    city = models.CharField(max_length=200)
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
    non_disclose = JSONField(default=None, null=True)
    default_registrant = models.NullBooleanField(null=True, )
    user = models.ForeignKey('auth.User',
                             related_name='personal_details',
                             on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'default_registrant',)

    def __str__(self):
        return self.surname + ', ' + self.first_name


class ContactType(models.Model):
    """
    Types of registry contacts.
    """
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    def __str__(self):
        return self.name


class TopLevelDomain(models.Model):
    """
    Domain ending model

    Note: for *reasons*, TLDs will be called *zones* inside the application.
    """
    # TLD
    zone = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.tld

    def _get_tld(self):
        return idna.decode(self.zone)

    def _get_slug(self):
        return re.sub('\.', '', self.zone)

    tld = property(_get_tld)

    def save(self, *args, **kwargs):
        self.zone = idna.encode(self.zone, uts46=True).decode('ascii')
        self.slug = re.sub('\.', '', self.zone)
        super(TopLevelDomain, self).save(*args, **kwargs)


class DomainProvider(models.Model):
    """
    Registries/rars providing top level domain services
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    active = models.BooleanField(default=True)

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
    user = models.ForeignKey('auth.User',
                             related_name='registrants',
                             on_delete=models.CASCADE)

    INT = 'int'
    LOC = 'loc'
    POSTAL_INFO_TYPES = (
        (INT, 'international'),
        (LOC, 'local'),
    )
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    telephone = models.CharField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    street = JSONField(default=None, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True, blank=True)
    status = JSONField(null=True, default=None)
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
    non_disclose = JSONField(default=None, null=True)
    account_template = models.ForeignKey(AccountDetail)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s - %s  provider: %s account_template: %s" % (self.pk,
                                                               self.name,
                                                               self.provider.slug,
                                                               self.account_template.id)


class Contact(models.Model):
    """
    Registry identifier for a contact registry_id.
    """
    INT = 'int'
    LOC = 'loc'
    POSTAL_INFO_TYPES = (
        (INT, 'international'),
        (LOC, 'local'),
    )
    name = models.CharField(max_length=200, null=True)
    email = models.CharField(max_length=200, null=True)
    telephone = models.CharField(max_length=200, null=True, blank=True)
    fax = models.CharField(max_length=200, null=True, blank=True)
    company = models.CharField(max_length=200, null=True, blank=True)
    street = JSONField(default=None, null=True)
    city = models.CharField(max_length=200, null=True)
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
    non_disclose = JSONField(default=None, null=True)
    provider = models.ForeignKey(DomainProvider)
    status = JSONField(null=True, default=None)
    # Id from provider
    registry_id = models.CharField(max_length=200, unique=True)
    user = models.ForeignKey('auth.User',
                             related_name='contacts',
                             on_delete=models.CASCADE)
    account_template = models.ForeignKey(AccountDetail)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return "%s - %s  provider: %s account_template: %s" % (self.pk,
                                                               self.name,
                                                               self.provider.slug,
                                                               self.account_template.id)


class TopLevelDomainProvider(models.Model):
    """
    Match a provider with a TLD.
    """

    zone = models.ForeignKey(TopLevelDomain)
    provider = models.ForeignKey(DomainProvider)
    expiration_notification_period_days = models.IntegerField(default=30)
    renewal_period = models.IntegerField(default=30)
    grace_period_days = models.IntegerField(default=30)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.zone.zone + " " + self.provider.name


class RegisteredDomain(models.Model):
    """
    Represent a registered domain name.

    A registered domain is a combined Domain + TopLevelDomainProvider
    object as it may be possible to register the same tld from multiple sources.
    Providers may have their own unique rules around renewal period and
    notifications.
    """
    name = models.CharField(max_length=200)
    fqdn = models.CharField(null=True,
                            unique=False,
                            default=uuid.uuid4,
                            max_length=200)
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
    registrant = models.ForeignKey(Registrant)
    authcode = models.CharField(max_length=100, null=True)
    roid = models.CharField(max_length=100, null=True)
    status = JSONField(default=None, null=True)
    nameservers = JSONField(default=None, null=True)
    expiration = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        """
        Represent a registered domain (i.e. name.tld).
        """
        return self.name + "." + self.tld.zone

    def _get_domain(self):
        return idna.decode(self.name)

    domain = property(_get_domain)

    def save(self, *args, **kwargs):
        """
        Override the save method
        """
        self.name = idna.encode(self.name, uts46=True).decode('ascii')
        self.tld = self.tld_provider.zone
        self.fqdn = self.name + "." + self.tld.zone
        super(RegisteredDomain, self).save(*args, **kwargs)

    class Meta:
        unique_together = ('name', 'tld', 'active',)



class DomainContact(models.Model):
    """
    Contact associated with a domain. A domain can have several contact
    registry_ids (depending on the registry).
    """
    registered_domain = models.ForeignKey(RegisteredDomain,
                                          related_name='contacts')
    contact = models.ForeignKey(Contact)
    contact_type = models.ForeignKey(ContactType)
    active = models.NullBooleanField(null=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('registered_domain', 'contact_type', 'contact',
                           'active')


class Nameserver(models.Model):

    """
    Nameserver object.
    """
    idn_host = models.CharField(max_length=255, unique=True)
    addr = JSONField(default=None, null=True)
    tld_provider = models.ForeignKey(TopLevelDomainProvider)
    default = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    status = JSONField(default=None, null=True)
    roid = models.CharField(max_length=100, null=True)
    user = models.ForeignKey('auth.User',
                             related_name='nameservers',
                             on_delete=models.CASCADE)

    def _get_nameserver(self):
        """
        Return unicode version of host
        :returns: str

        """
        return idna.decode(self.idn_host)

    host = property(_get_nameserver)

    def save(self, *args, **kwargs):
        self.idn_host = idna.encode(self.idn_host, uts46=True).decode('ascii')
        super(Nameserver, self).save(*args, **kwargs)


class DefaultAccountTemplate(models.Model):

    """
    Store some default details for a given project.
    """

    user = models.ForeignKey('auth.User',
                             related_name='default_account',
                             on_delete=models.CASCADE)
    account_template = models.ForeignKey(AccountDetail)
    provider = models.ForeignKey(DomainProvider)

    def __str__(self):
        return self.account_template.first_name + " " + self.account_template.surname + " - " + self.provider.name

    class Meta:
        unique_together = ('user', 'provider', 'account_template',)


class DefaultAccountContact(models.Model):
    """
    Assign default contact for registry.
    """
    user = models.ForeignKey('auth.User',
                             related_name='default_account_contact',
                             on_delete=models.CASCADE)
    account_template = models.ForeignKey(AccountDetail)
    contact_type = models.ForeignKey(ContactType)
    provider = models.ForeignKey(DomainProvider)
    mandatory = models.BooleanField(default=False)

    def __str__(self):
        return self.provider.name + " - " + self.contact_type.name

    class Meta:
        unique_together = ('user', 'contact_type', 'account_template',
                           'provider', 'mandatory',)
