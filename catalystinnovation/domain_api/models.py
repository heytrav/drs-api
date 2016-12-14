from django.db import models

class Person(models.Model):

    """Person object in db"""
    first_name = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
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

class TopLevelDomain(models.Model):

    """Domain ending model"""
    zone = models.CharField(max_length=100)
    description = models.TextField()

class DomainProvider(models.Model):

    """Registries/rars providing top level domain services"""
    name = models.CharField(max_length=100)
    description = models.TextField()
    zones = models.ManyToManyField(TopLevelDomain)
