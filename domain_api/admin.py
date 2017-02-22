from django.contrib import admin

from .models import (
    PersonalDetail,
    TopLevelDomain,
    DomainProvider,
    TopLevelDomainProvider,
    Domain,
    RegisteredDomain,
    Registrant,
    Contact,
    DomainRegistrant,
    DomainContact,
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


admin.site.register(PersonalDetail)
admin.site.register(TopLevelDomain)
admin.site.register(DomainProvider, DomainProviderAdmin)
admin.site.register(Domain)
admin.site.register(RegisteredDomain)
admin.site.register(Registrant)
admin.site.register(Contact)
admin.site.register(DomainRegistrant)
admin.site.register(DomainContact)
