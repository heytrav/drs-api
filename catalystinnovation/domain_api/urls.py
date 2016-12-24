from django.conf.urls import url, include
from domain_api import views
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'identities', views.IdentityViewSet)
router.register(r'personal-details', views.PersonalDetailViewSet)
router.register(r'contact-types', views.ContactTypeViewSet)
router.register(r'contact-handles', views.ContactHandleViewSet)
router.register(r'tlds', views.TopLevelDomainViewSet)
router.register(r'tld-providers', views.TopLevelDomainProviderViewSet)
router.register(r'domain-providers', views.DomainProviderViewSet)
router.register(r'domains', views.DomainViewSet)
router.register(r'registrant-handles', views.RegistrantHandleViewSet)
router.register(r'registered-domains', views.RegisteredDomainViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
]
