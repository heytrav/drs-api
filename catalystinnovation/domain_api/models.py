from django.db import models

class Identity(models.Model):

    """
    Identity object in db.
    """
    first_name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200, blank=True)
    username = models.CharField(max_length=100, unique=True)

    def __str__(self):
        """String representation
        :returns: TODO

        """
        return self.surname + ', ' + self.first_name


class PersonalDetail(models.Model):
    """
    Person object in db.
    """

    identity = models.ForeignKey(Identity)
    email = models.CharField(max_length=200)
    email2 = models.CharField(max_length=200, blank=True)
    email3 = models.CharField(max_length=200, blank=True)
    house_number = models.CharField(max_length=10)
    street1 = models.CharField(max_length=200)
    street2 = models.CharField(max_length=200, blank=True)
    street3 = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200)
    suburb = models.CharField(max_length=200, blank=True)
    state = models.CharField(max_length=200, blank=True)
    postcode = models.CharField(max_length=20)
    country = models.CharField(max_length=200)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    def __str__(self):
        """String representation
        :returns: TODO

        """
        return self.identity.surname + ', ' + self.identity.first_name


class ContactType(models.Model):
    """
    Types of registry contacts.
    """
    name = models.CharField(max_length=50)
    description = models.TextField()


class TopLevelDomain(models.Model):
    """Domain ending model

    Note: for *reasons*, TLDs will be called *zones* inside the application.
    """
    # TLD
    zone = models.CharField(max_length=100, unique=True)
    # Internationalised syntax: xn--*
    idn_zone = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    def __str__(self):
        """String representation

        """
        return self.zone


class DomainProvider(models.Model):
    """
    Registries/rars providing top level domain services
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField()

    def __str__(self):
        """String representation
        :returns: name

        """
        return self.name


class RegistrantHandle(models.Model):
    """
    Registry identifier for a registrant contact.

    This type of contact can only be a registrant for a domain.
    """
    person = models.ForeignKey(PersonalDetail)
    provider = models.ForeignKey(DomainProvider)
    # Id from provider
    handle = models.CharField(max_length=200)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)


class ContactHandle(models.Model):
    """
    Registry identifier for a contact handle.

    This type of contact

    - admin
    - tech
    - billing
    - zone?

    There may be other types.
    """
    person = models.ForeignKey(PersonalDetail)
    contact_type = models.ForeignKey(ContactType)
    provider = models.ForeignKey(DomainProvider)
    # Id from provider
    handle = models.CharField(max_length=200)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)


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
        """String representation
        :returns: Zone and provider name

        """
        return self.zone.zone + " " + self.provider.name


class Domain(models.Model):
    """
    Represent a domain.
    """
    # The part of a domain name before the tld
    name = models.CharField(max_length=200, unique=True)
    # punyencoded version of the name field. For ascii domains this will
    # be identical to name.
    idn = models.CharField(max_length=300, unique=True)

    def __str__(self):
        """String representation
        :returns: TODO

        """
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
    anniversary = models.DateField()
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

    class Meta:
        unique_together = ('domain', 'tld', 'active')

    def __str__(self):
        """Represent a registered domain (i.e. name.tld)."""
        return self.domain.name + "." + self.tld_provider.zone.zone


class DomainRegistrant(models.Model):
    """
    Registrant associated with a domain. A domain can typically have only one.
    """
    registered_domain = models.ForeignKey(RegisteredDomain)
    registrant = models.ForeignKey(RegistrantHandle)
    active = models.NullBooleanField(null=True)
    created = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('registered_domain', 'registrant', 'active')

class DomainHandles(models.Model):
    """
    Contacts associated with a domain. A domain can have several contact handles
    (depending on the registry).
    """
    registered_domain = models.ForeignKey(RegisteredDomain)
    contact_handle = models.ForeignKey(ContactHandle)
    active = models.NullBooleanField(null=True)
    created = models.DateField(auto_now_add=True)

    class Meta:
        unique_together = ('registered_domain', 'contact_handle', 'active')
