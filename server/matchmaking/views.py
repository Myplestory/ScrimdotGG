from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db.models import Avg
from django.http import JsonResponse
from scrimgg.models import Player, Lobby, Match
from scrimgg.serializers import PlayerSerializer, LobbySerializer, MatchSerializer
import json, random


@api_view(['POST'])
def queue_up(request):
    return

@api_view(['POST'])
def queue_upbypass(request):
    data = json.loads(request.body)
    try:
        player = Player.objects.get(puuid=data['puuid'])
        lobby = Lobby.objects.get(id=data['lobbyid'])
        parties_dict = {
            'team A': [], 
            'team B': []   
        }
        players_in_lobby = lobby.players.all()
        for player in players_in_lobby:
            parties_dict['team A'].append(str(player.puuid))
        print(parties_dict)
        if len(data['mapchoices']) and len(data['serverchoices']) == 1:
          match = Match.objects.create(
            maps=data['mapchoices'],
            played_map=data.get('played_map', data['mapchoices'][0]),
            played_server = data.get('played_server', data['serverchoices'][0]),
            parties=parties_dict,
            match_info=data.get('match_info', {})
          )
          match.save()
          all_players = parties_dict['team A'] + parties_dict['team B']
          selected_puuid = random.choice(all_players)
          print({"message": "Successfully got in game!", "status": "build" ,"match_id": match.id, "match_map":match.played_map,"match_server":match.played_server,"constructor":selected_puuid})
          return JsonResponse({"message": "Successfully got in game!", "status": "build" ,"match_id": match.id, "match_map":match.played_map,"match_server":match.played_server,"constructor":selected_puuid}, status=status.HTTP_200_OK)
        else:
          match = Match.objects.create(
              maps=data['mapchoices'],
              banned_maps=data['banned_maps'],
              played_map=data.get('played_map', ''),
              start_time=data.get('start_time', None), # or auto_now_add=True
              finish_time=data.get('finish_time', None), # or auto_now_add=True
              parties=parties_dict,
              match_info=data.get('match_info', {})
          )
          match.players.add(player)
          match.save()
          serializer = MatchSerializer(match)
          return Response(serializer.data, status=status.HTTP_200_OK)

    except Player.DoesNotExist:
        return JsonResponse({"error": "Player not found."}, status=404)
    except Lobby.DoesNotExist:
        return JsonResponse({"error": "Lobby not found."}, status=404)
    except Exception as e:
        # Handle other possible exceptions
        return JsonResponse({"error": str(e)}, status=500)
  
@api_view(['PUT'])
def dequeue(request):
  print(request)
  
@api_view(['POST'])
def setroom(request):
    data = json.loads(request.body)
    try:
        match_id = data.get('match_id')
        pregame_id = data.get('pregame_id')
        if not match_id or not pregame_id:
            return JsonResponse({"error": "Both 'match_id' and 'pregame_id' are required."}, status=400)
        match = Match.objects.get(id=match_id)
        match.pregame_id = pregame_id
        match.save()
        return JsonResponse({"message": "pregame_id set successfully"}, status=200)
    except Match.DoesNotExist:
        return JsonResponse({"error": "Match not found."}, status=404)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
    
@api_view(['POST'])
def fetchroom(request):
    data = json.loads(request.body)
    try:
        match_id = data.get('match_id')
        if not match_id:
            return JsonResponse({"error": "The 'match_id' is required."}, status=400)
        match = Match.objects.get(id=match_id)
        return JsonResponse({"pregame_id": match.pregame_id}, status=200)
    except Match.DoesNotExist:
        return JsonResponse({"error": "Match not found."}, status=404)
    except KeyError:
        return JsonResponse({"error": "Missing 'match_id' in request."}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)