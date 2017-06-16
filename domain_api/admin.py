from django.contrib import admin

from .models import (
    AccountDetail,
    TopLevelDomain,
    DomainProvider,
    TopLevelDomainProvider,
    RegisteredDomain,
    Registrant,
    Contact,
    ContactType,
    DomainContact,
    DefaultAccountTemplate,
    DefaultRegistrant,
    DefaultContact,
    DefaultAccountContact,
    Nameserver
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

class TopLevelDomainAdmin(admin.ModelAdmin):
    list_display = ('tld', 'slug', 'zone', 'description')
    readonly_fields = ('tld', 'slug',)

    fieldsets = [
        (None, {'fields': ['tld', 'zone', 'slug']}),
        ('Description', {'fields': ['description']})
    ]

admin.site.register(DefaultAccountTemplate)
admin.site.register(DefaultAccountContact)
admin.site.register(DefaultRegistrant)
admin.site.register(DefaultContact)
admin.site.register(AccountDetail)
admin.site.register(TopLevelDomain, TopLevelDomainAdmin)
admin.site.register(DomainProvider, DomainProviderAdmin)
admin.site.register(RegisteredDomain)
admin.site.register(Registrant)
admin.site.register(Contact)
admin.site.register(ContactType)
admin.site.register(DomainContact)
