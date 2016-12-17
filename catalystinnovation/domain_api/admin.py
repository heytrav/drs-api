from django.contrib import admin

from .models import (
    Identity,
    PersonalDetail,
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

class PersonalDetailsInline(admin.StackedInline):
    model = PersonalDetail
    extra = 2

class IdentityAdmin(admin.ModelAdmin):
    inlines = [PersonalDetailsInline]







admin.site.register(Identity, IdentityAdmin)
admin.site.register(TopLevelDomain)
admin.site.register(DomainProvider, DomainProviderAdmin)
admin.site.register(Domain)
admin.site.register(RegisteredDomain)
