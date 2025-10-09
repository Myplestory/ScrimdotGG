from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_player, name='register_player'),
    path('update/<int:pk>/', views.update_player, name='update_player'),
    path('stats/<int:pk>/', views.player_stats, name='player_stats'),
    path('history/<int:pk>/', views.player_history, name='player_history'),
    path('request_add_friend/<int:pk>/', views.request_add_friend, name='request_add_friend'),
    path('confirm_add_friend/<int:pk>/', views.confirm_add_friend, name='confirm_add_friend'),
    path('remove_friend/<int:pk>/', views.remove_friend, name='remove_friend'),
]