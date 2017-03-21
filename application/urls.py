"""catalystinnovation URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.contrib import admin
from rest_framework_swagger.views import get_swagger_view
from rest_framework_jwt.views import (
    obtain_jwt_token,
    verify_jwt_token,
    refresh_jwt_token
)
from domain_api.views import CreateUserView

schema_view = get_swagger_view(title='Domain API')


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^v1/', include('domain_api.urls')),
    url(r'^api-auth/', include('rest_framework.urls',
                               namespace='rest_framework')),
    url(r'^api-token-auth', obtain_jwt_token),
    url(r'^api-token-refresh', refresh_jwt_token),
    url(r'^api-token-verify', verify_jwt_token),
    url('^schema/$', schema_view),
    url(r'^register/$', CreateUserView.as_view(), name="create-user"),
]
