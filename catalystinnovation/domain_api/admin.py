from django.contrib import admin

from .models import (
    Person,
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







admin.site.register(Person)
admin.site.register(TopLevelDomain)
admin.site.register(DomainProvider, DomainProviderAdmin)
admin.site.register(Domain)
admin.site.register(RegisteredDomain)
