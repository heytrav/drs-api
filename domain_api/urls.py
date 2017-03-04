from django.conf.urls import url, include
from domain_api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'personal-detail', views.PersonalDetailViewSet, "personal")
router.register(r'contact-types', views.ContactTypeViewSet)
router.register(r'contacts', views.ContactViewSet, "contact")
router.register(r'tld', views.TopLevelDomainViewSet)
router.register(r'tld-provider', views.TopLevelDomainProviderViewSet)
router.register(r'domain-provider', views.DomainProviderViewSet)
router.register(r'domain', views.DomainViewSet, "domain")
router.register(r'registrant', views.RegistrantViewSet, "registrant")
router.register(
    r'registered-domain',
    views.RegisteredDomainViewSet,
    "registereddomain"
)
router.register(
    r'domain-registrant',
    views.DomainRegistrantViewSet, "domainregistrant"
)
router.register(r'domain-contact', views.DomainContactViewSet, "domaincontact")
router.register(r'users', views.UserViewSet)

domain_list = views.DomainRegistryManagementViewset.as_view({
    'get': 'list',
    'post': 'create'
})
domain_detail = views.DomainRegistryManagementViewset.as_view({
    'get': 'info',
})
domain_single_check = views.DomainRegistryManagementViewset.as_view({
    'get': 'available'
})

domain_bulk_check = views.DomainRegistryManagementViewset.as_view({
    'post': 'available'
})


urlpatterns = [
    url(r'^', include(router.urls, namespace='domain_api')),
    url(r'^check-domain/(?P<domain>.*)/$', views.check_domain),
    url(r'^info-domain/(?P<domain>.*)/$', views.info_domain),
    url(r'^info-contact/(?P<contact>[^\/]+)/(?P<registry>.*)/$',
        views.info_contact),
    url(r'^info-contact/(?P<contact>.*)/$', views.info_contact),
    url(r'^contact-domains/(?P<registry_id>.*)/$', views.contact_domains),
    url(r'^registry-contact/$', views.registry_contact),
    url(
        r'^registry-contact/(?P<registry>.*)/(?P<contact_type>.*)/$',
        views.registry_contact
    ),
    url(r'^register-domain/$', views.register_domain),
    url(r'^domains/$', domain_list, name='domain-list'),
    url(
        r'^domains/available/(?P<domain>.*)/$',
        domain_single_check, name='check-domain'
    ),
    url(
        r'^domains/bulk-available/$',
        domain_bulk_check,
        name='domain-bulk-available'
    ),
    url(r'^domains/(?P<domain>.*)/$', domain_detail, name='domain-info'),
]
