from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Player
from .serializers import PlayerSerializer, PlayerStatsSerializer

@api_view(['POST'])
def register_player(request):
    # Logic to register a new player
    pass

@api_view(['PUT'])
def update_player(request, pk):
    # Logic to update player information
    pass

@api_view(['GET', 'PUT'])
def player_stats(request, pk):
    # Logic to retrieve or update player stats
    pass

@api_view(['GET'])
def player_history(request, pk):
    # Logic to view a player's match history
    pass
  
@api_view(['PUT'])
def request_add_friend(request, pk):
    # Logic to update player information
    pass

@api_view(['PUT'])
def confirm_add_friend(request, pk):
    # Logic to update player information
    pass

@api_view(['PUT'])
def remove_friend(request, pk):
    # Logic to update player information
    pass