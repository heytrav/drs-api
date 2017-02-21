from django.contrib import admin

from .models import (
    PersonalDetail,
    TopLevelDomain,
    DomainProvider,
    TopLevelDomainProvider,
    Domain,
    RegisteredDomain,
    RegistrantHandle,
    ContactHandle,
    DomainRegistrant,
    DomainHandles,
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
admin.site.register(RegistrantHandle)
admin.site.register(ContactHandle)
admin.site.register(DomainRegistrant)
admin.site.register(DomainHandles)
