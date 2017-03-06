from django.conf.urls import url, include
from domain_api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register('defaultaccounttemplate-detail',
                views.DefaultAccountTemplateViewSet,
                "defaultaccounttemplate")
router.register(r'account-detail', views.AccountDetailViewSet, "account")
router.register(r'contact-types', views.ContactTypeViewSet)
router.register(r'contact', views.ContactViewSet, "contact")
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
    'get': 'domain_set',
    'post': 'create'
})
domain_detail = views.DomainRegistryManagementViewset.as_view({
    'get': 'info',
})
domain_single_check = views.DomainRegistryManagementViewset.as_view({
    'get': 'available'
})

domain_bulk_check = views.DomainRegistryManagementViewset.as_view({
    'get': 'bulk_available'
})

contact_detail = views.ContactManagementViewset.as_view({
    'get': 'info'
})
contact_list = views.ContactManagementViewset.as_view({
    'get': 'list'
})
registrant_detail = views.RegistrantManagementViewset.as_view({
    'get': 'info'
})
registrant_list = views.RegistrantManagementViewset.as_view({
    'get': 'list'
})

urlpatterns = [
    url(r'^', include(router.urls, namespace='domain_api')),
    url(r'^registry-contact/$', views.registry_contact),
    url(
        r'^registry-contact/(?P<registry>.*)/(?P<contact_type>.*)/$',
        views.registry_contact
    ),
    url(r'^domains/$', domain_list, name='domain-list'),
    url(
        r'^domains/available/(?P<name>[^\.\/]+)/$',
        domain_bulk_check,
        name='domain-bulk-available'
    ),
    url(
        r'^domains/available/(?P<domain>.*)/$',
        domain_single_check, name='check-domain'
    ),
    url(r'^domains/create/$', domain_list, name='domain-create'),
    url(r'^domains/(?P<domain>.*)/$', domain_detail, name='domain-info'),
    url(r'^contacts/(?P<registry_id>.*)/$',
        contact_detail,
        name='contact-info'),
    url(r'^contacts/(?P<registry_id>[^\/]+)/(?P<registry>.*)/$',
        contact_detail,
        name='contact-info'),
    url('^contacts/$', contact_list, name='contact-list'),
    url(r'^registrants/(?P<registry_id>.*)/$',
        registrant_detail,
        name='registrant-info'),
    url(r'^registrants/(?P<registry_id>[^\/]+)/(?P<registry>.*)/$',
        registrant_detail,
        name='registrant-info'),
    url('^registrants/$', registrant_list, name='contact-list'),
]
