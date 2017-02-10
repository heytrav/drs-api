from django.conf.urls import url, include
from domain_api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'personal-detail', views.PersonalDetailViewSet, "personal")
router.register(r'contact-types', views.ContactTypeViewSet)
router.register(r'contact-handles', views.ContactHandleViewSet, "contacthandle")
router.register(r'tlds', views.TopLevelDomainViewSet)
router.register(r'tld-providers', views.TopLevelDomainProviderViewSet)
router.register(r'domain-providers', views.DomainProviderViewSet)
router.register(r'domains', views.DomainViewSet, "domain")
router.register(r'registrant-handles', views.RegistrantHandleViewSet, "registranthandle")
router.register(r'registered-domains', views.RegisteredDomainViewSet, "registereddomain")
router.register(r'domain-registrant', views.DomainRegistrantViewSet, "domainregistrant")
router.register(r'domain-handle', views.DomainHandleViewSet, "domainhandles")
router.register(r'users', views.UserViewSet)

urlpatterns = [
    url(r'^', include(router.urls, namespace='domain_api')),
    url(r'^check-domain/(?P<registry>[^\/]+)/(?P<domain>.*)/$', views.check_domain),
    url(r'^info-domain/(?P<registry>[^\/]+)/(?P<domain>.*)/$', views.info_domain),
    url(r'^registry-contact/$', views.registry_contact),
    url(r'^registry-contact/(?P<registry>.*)/(?P<contact_type>.*)/$', views.registry_contact),
    url(r'^register-domain/(?P<registry>[^\/]+)/$', views.register_domain),
]
