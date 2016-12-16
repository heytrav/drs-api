from django.db import models

class Person(models.Model):

    """Person object in db"""
    first_name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    middle_name = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=200)
    emai2 = models.CharField(max_length=200, blank=True)
    emai3 = models.CharField(max_length=200, blank=True)
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


class TopLevelDomain(models.Model):

    """Domain ending model

    Note: for *reasons*, TLDs will be called *zones* inside the application.
    """
    # TLD
    zone = models.CharField(max_length=100)
    # Internationalised syntax: xn--*
    idn_zone = models.CharField(max_length=100)
    description = models.TextField()
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)

class DomainProvider(models.Model):

    """Registries/rars providing top level domain services"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    # TLDs provided
    zones = models.ManyToManyField(TopLevelDomain)


class Domain(models.Model):

    """Represent a domain"""
    # The part of a domain name before the tld
    name = models.CharField(max_length=200)
    idn = models.CharField(max_length=300)

    # Expressed in number of years
    registration_period = models.IntegerField()

    # This will need to be a meta field that is calculated based on the
    # registration period and whatever the notification buffer is for a
    # provider. The aim is to notify a customer ahead of time that their domain
    # is about to renew/expire.
    #anniversary = models.DateField()
    auto_renew = models.BooleanField(default=True)
    created = models.DateField(auto_now_add=True)
    updated = models.DateField(auto_now=True)


