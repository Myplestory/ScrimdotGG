"""
URL configuration for ScrimGG project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import TemplateView
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/check_authentication/', views.check_authentication, name='check_authentication'),
    path('api/logout/', views.logout_view, name='logout'),
    path('api/csrf_cookie/', views.getCSRFToken, name='getCSRFToken'),
    path('login/', include('riotlogin.urls'), name='oauth2'),
    path('lobby/', include('lobby.urls'), name='lobby'),
    path('matchmaking/', include('matchmaking.urls'), name='matchmaking'),
    # path('oauth2/', include('riotlogin.urls'), name='oauth2'),
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    re_path(r'^.*$', TemplateView.as_view(template_name='404.html'), name='404'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
