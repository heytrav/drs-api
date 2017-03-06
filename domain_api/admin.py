from django.contrib import admin

from .models import (
    AccountDetail,
    TopLevelDomain,
    DomainProvider,
    TopLevelDomainProvider,
    Domain,
    RegisteredDomain,
    Registrant,
    Contact,
    ContactType,
    DomainRegistrant,
    DomainContact,
    DefaultAccountTemplate,
    DefaultRegistrant,
    DefaultContact,
)


class TopLevelDomainProviderInline(admin.TabularInline):
    model = TopLevelDomainProvider
    extra = 3


class DomainProviderAdmin(admin.ModelAdmin):

    """Admin for domain providers."""

    fieldsets = [
        (None, {'fields': ['name']}),
        ('Slug', {'fields': ['slug']}),
        ('Description', {'fields': ['description']})
    ]
    inlines = [TopLevelDomainProviderInline]

admin.site.register(DefaultAccountTemplate)
admin.site.register(DefaultRegistrant)
admin.site.register(DefaultContact)
admin.site.register(AccountDetail)
admin.site.register(TopLevelDomain)
admin.site.register(DomainProvider, DomainProviderAdmin)
admin.site.register(Domain)
admin.site.register(RegisteredDomain)
admin.site.register(Registrant)
admin.site.register(Contact)
admin.site.register(ContactType)
admin.site.register(DomainRegistrant)
admin.site.register(DomainContact)
