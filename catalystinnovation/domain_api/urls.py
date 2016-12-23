from django.conf.urls import url
from domain_api import views

urlpatterns = [
    url(r'^$', views.api_root),
    url(r'^identities/$',
        views.IdentityList.as_view(),
        name='identity-list'),
    url(r'^identities/(?P<pk>[0-9]+)/$',
        views.IdentityDetail.as_view(),
        name='identity-detail'),
    url(r'^users/$',
        views.UserList.as_view(),
        name='user-list'),
    url(r'^users/(?P<pk>[0-9]+)/$',
        views.UserDetail.as_view(),
        name='user-detail'),
]
