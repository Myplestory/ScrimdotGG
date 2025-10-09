from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_lobby, name='create_lobby'),
    path('delete/', views.delete_lobby, name='delete_lobby'),
    path('join/<int:lobby_id>/', views.join_lobby, name='join_lobby'),
    path('leave/<int:lobby_id>/', views.leave_lobby, name='leave_lobby'),
    path('detail/<int:lobby_id>/', views.lobby_details, name='lobby_details'),
]