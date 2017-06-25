from django.conf.urls import url, include
from domain_api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'account-details', views.AccountDetailViewSet, "account")
router.register(r'contact-types', views.ContactTypeViewSet)
router.register(r'manage-contacts', views.ContactViewSet, "contact")
router.register(r'tlds', views.TopLevelDomainViewSet)
router.register(r'tld-providers', views.TopLevelDomainProviderViewSet)
router.register(r'registries', views.DomainProviderViewSet)
router.register(r'domain-registrants', views.RegistrantViewSet, "registrant")
router.register(
    r'registered-domains',
    views.RegisteredDomainViewSet,
    "registereddomain"
)
router.register('nameservers', views.NameserverViewSet, 'nameserver')
router.register(r'domain-contacts', views.DomainContactViewSet, "domaincontact")
router.register(r'users', views.UserViewSet)
default_account = views.DefaultAccountTemplateViewSet.as_view({
    'get': 'list_accounts',
    'post': 'create',
})
default_account_manage = views.DefaultAccountTemplateViewSet.as_view({
    'delete': 'delete_account',
    'put': 'update',
    'get': 'detail'
})
domain_list = views.DomainRegistryManagementViewSet.as_view({
    'get': 'domain_set',
    'post': 'create'
})
domain_detail = views.DomainRegistryManagementViewSet.as_view({
    'get': 'info',
    'patch': 'update'
})
domain_single_check = views.DomainAvailabilityViewSet.as_view({
    'get': 'available'
})

domain_bulk_check = views.DomainAvailabilityViewSet.as_view({
    'get': 'bulk_available'
})

contact_detail = views.ContactManagementViewSet.as_view({
    'get': 'info',
    'patch': 'update'
})
contact_list = views.ContactManagementViewSet.as_view({
    'get': 'list_contacts'
})
registrant_detail = views.RegistrantManagementViewSet.as_view({
    'get': 'info',
    'patch': 'update'
})
registrant_list = views.RegistrantManagementViewSet.as_view({
    'get': 'list_contacts'
})

host_single_check = views.HostManagementViewSet.as_view({
    'get': 'available'
})
host_list = views.HostManagementViewSet.as_view({
    'get': 'host_set',
    'post': 'create'
})
host_detail = views.HostManagementViewSet.as_view({
    'get': 'info',
})


urlpatterns = [
    url(r'^', include(router.urls, namespace='domain_api')),
    url(r'^domains/$', domain_list, name='domain-list'),
    url(
        r'^available/(?P<name>[^\.\/]+)/$',
        domain_bulk_check,
        name='domain-bulk-available'
    ),
    url(
        r'^available/(?P<domain>.*)/$',
        domain_single_check, name='check-domain'
    ),
    url(r'^domains/(?P<domain>.*)/$', domain_detail, name='domain-info'),
    url(r'^contacts/(?P<registry_id>.*)/$',
        contact_detail,
        name='contact-info'),
    url('^contacts/$', contact_list, name='contact-list'),
    url(r'^registrants/(?P<registry_id>.*)/$',
        registrant_detail,
        name='registrant-info'),
    url('^registrants/$', registrant_list, name='contact-list'),
    url(r'^account/default/$', default_account, name='default-account'),
    url(r'^account/default/(?P<default_id>.*)/$', default_account_manage,
        name='default-account-manage'),
    url(
        r'^hosts/available/(?P<host>.*)/$',
        host_single_check, name='check-host'
    ),
    url(r'^hosts/$', host_list, name='host-list'),
    url(r'^hosts/(?P<host>.*)/$', host_detail, name='host-info'),
]
