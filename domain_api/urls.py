from django.conf.urls import url, include
from domain_api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'account-details', views.AccountDetailViewSet, "account")
router.register(r'contact-types', views.ContactTypeViewSet)
router.register(r'contacts', views.ContactViewSet, "contact")
router.register(r'tlds', views.TopLevelDomainViewSet)
router.register(r'tld-providers', views.TopLevelDomainProviderViewSet)
router.register(r'registries', views.DomainProviderViewSet)
router.register(r'registrants', views.RegistrantViewSet, "registrant")
router.register(
    r'domains',
    views.RegisteredDomainViewSet,
    "registereddomain"
)
router.register(r'nameservers', views.NameserverViewSet, 'nameserver')
router.register(r'domain-contacts', views.DomainContactViewSet, "domaincontact")
router.register(r'users', views.UserViewSet)
router.register(r'default-templates', views.DefaultAccountTemplateViewSet,
                'defaultaccounttemplate')
router.register(r'default-contacts', views.DefaultAccountContactViewSet,
                'defaultaccountcontact')
domain_single_check = views.DomainAvailabilityViewSet.as_view({
    'get': 'available'
})

domain_bulk_check = views.DomainAvailabilityViewSet.as_view({
    'get': 'bulk_available'
})

host_single_check = views.HostAvailabilityViewSet.as_view({
    'get': 'available'
})


urlpatterns = [
    url(r'^', include(router.urls, namespace='domain_api')),
    url(
        r'^available/(?P<name>[^\.\/]+)/$',
        domain_bulk_check,
        name='domain-bulk-available'
    ),
    url(
        r'^available/(?P<domain>.*)/$',
        domain_single_check, name='check-domain'
    ),
    url(
        r'^hosts/available/(?P<host>.*)/$',
        host_single_check, name='check-host'
    ),
]
