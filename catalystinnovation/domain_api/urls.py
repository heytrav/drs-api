from django.conf.urls import url
from rest_framework.urlpatterns import format_suffix_patterns
from domain_api import views

urlpatterns = [
    url('^domain-api/$', views.IdentityList.as_view()),
    url('^domain-api/(?P<pk>[0-9]+)/$', views.IdentityDetail.as_view()),
]

