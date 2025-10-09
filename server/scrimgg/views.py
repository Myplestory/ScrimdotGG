from rest_framework.decorators import api_view, permission_classes
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import JsonResponse
from django.contrib.auth import logout
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from scrimgg.models import Player

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def check_authentication(request):
    # Get the authenticated user
    user = request.user
    user_data = {
        "message": "Authenticated",
        "first_name": user.first_name,
        "username": user.email,
    }
    return JsonResponse(user_data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    # Log the user out
    logout(request)
    response_data = {
        "message": "Log out success"
    }
    return JsonResponse(response_data, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
@ensure_csrf_cookie
def getCSRFToken(request):
    return JsonResponse({ 'success': 'CSRF cookie set' }, status=200)

