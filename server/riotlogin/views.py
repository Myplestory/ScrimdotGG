from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate
from django.http import HttpRequest, JsonResponse
from django.shortcuts import redirect
from scrimgg.models import Player
from valclient.client import Client
import json
import requests
import re
import os


@api_view(["POST"])
def riot_login(request):
    data = json.loads(request.body)
    puuid = data.get('puuid')
    region = data.get('region')
    username = data.get('username')
    alias = data.get('alias')
    print(data)
    try:
        custom_user, created = Player.objects.get_or_create(
            puuid=puuid, region=region, username=username, alias=alias
        )
        if created:
            print("Player created!")
        if not request.session.session_key:
            request.session.create()
        session_id = request.session.session_key
        print(f"Session ID: {session_id}")
        return JsonResponse({
            'message': 'Player created!' if created else 'Player found!',
            'sessionid': session_id
        }, status=200)
    except Exception as e:
        print('Error during login:', str(e))
        return JsonResponse({'message': 'An error occurred'}, status=500)

def home(request):
    return JsonResponse({'message': 'Home Page'})