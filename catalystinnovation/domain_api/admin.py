from django.contrib import admin

from .models import (
    Person,
    TopLevelDomain,
    DomainProvider,
    TopLevelDomainProvider,
    Domain,
    RegisteredDomain
)


class DomainProviderAdmin(admin.ModelAdmin):

    """Admin for domain providers."""

    fieldsets = [
        (None, {'fields': ['name']}),
        ('Description', {'fields': ['description']})
    ]




class TopLevelDomainProviderAdmin(admin.ModelAdmin):

    """Admin for top level domain providers."""




admin.site.register(Person)
admin.site.register(TopLevelDomain)
admin.site.register(DomainProvider, DomainProviderAdmin)
admin.site.register(TopLevelDomainProvider)
admin.site.register(Domain)
