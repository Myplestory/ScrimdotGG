from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Avg
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from scrimgg.models import Player, Lobby
from scrimgg.serializers import PlayerSerializer, LobbySerializer
import json

@api_view(['POST'])
def create_lobby(request):
    # Assume the request contains the player's ID to set as the lobby leader
    data = json.loads(request.body)
    player_id=data['puuid']
    if not player_id:
        return JsonResponse({"error": "Player ID is required."}, status=status.HTTP_400_BAD_REQUEST)
    try:
        player = Player.objects.get(puuid=player_id)
    except Player.DoesNotExist:
        return JsonResponse({"error": "Player not found."}, status=status.HTTP_404_NOT_FOUND)
    lobby = Lobby.objects.filter(lobby_leader=player, is_active=True).first()
    if lobby:
        serializer = LobbySerializer(lobby)
        return JsonResponse(serializer.data, status=status.HTTP_200_OK)
    else:
        new_lobby = Lobby.objects.create(lobby_leader=player)
        new_lobby.players.add(player)  
        new_lobby.size += 1  
        new_lobby.average_elo = new_lobby.players.aggregate(Avg('elo'))['elo__avg'] or 0
        new_lobby.save()
        # Calculate the average elo if necessary here
        serializer = LobbySerializer(new_lobby)
        return JsonResponse(serializer.data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
def delete_lobby(request):
    # Logic to register a new player
    pass

@api_view(['PUT'])
def join_lobby(request, pk):
    # Logic to update player information
    pass

@api_view(['PUT'])
def leave_lobby(request, pk):
    # Logic to retrieve or update player stats
    pass

@api_view(['GET'])
def player_history(request, pk):
    # Logic to view a player's match history
    pass

@api_view(['GET'])
def lobby_details(request, pk):
    try:
        player = Player.objects.get(pk=pk)
        serializer = PlayerSerializer(player)
        print(serializer)
        return Response(serializer.data)  # Use DRF's Response for built-in content negotiation and formatting
    except Player.DoesNotExist:
        return Response({'message': 'Player not found'}, status=404)