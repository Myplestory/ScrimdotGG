from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.riot_login, name='riot_login'),
    # path('login/redirect/', views.riot_login_redirect, name='riot_login_redirect'),
]