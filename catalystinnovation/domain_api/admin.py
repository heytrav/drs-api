from django.contrib import admin

from .models import (
    Identity,
    PersonalDetails,
    TopLevelDomain,
    DomainProvider,
    TopLevelDomainProvider,
    Domain,
    RegisteredDomain
)


class TopLevelDomainProviderInline(admin.TabularInline):
    model = TopLevelDomainProvider
    extra = 3

class DomainProviderAdmin(admin.ModelAdmin):

    """Admin for domain providers."""

    fieldsets = [
        (None, {'fields': ['name']}),
        ('Description', {'fields': ['description']})
    ]
    inlines = [TopLevelDomainProviderInline]







admin.site.register(Identity)
admin.site.register(PersonalDetails)
admin.site.register(TopLevelDomain)
admin.site.register(DomainProvider, DomainProviderAdmin)
admin.site.register(Domain)
admin.site.register(RegisteredDomain)
