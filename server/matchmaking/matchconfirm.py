import uuid
import json
from django.core.cache import cache
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.apps import apps


def initiate_match_confirmation(matched_players, matched_lobbies_ids):
    match_confirmation_id = str(uuid.uuid4())
    notified_key = f"match:{match_confirmation_id}:notified"
    lobbies_key = f"match:{match_confirmation_id}:lobbies"

    for player in matched_players:
        cache.sadd(notified_key, player.id)  # Track notified players
    for lobby_id in matched_lobbies_ids:
        cache.sadd(lobbies_key, lobby_id)  # Track involved lobbies

    cache.expire(notified_key, 300)  # 5 minutes
    cache.expire(lobbies_key, 300)

    return match_confirmation_id


def mark_acceptance(player_id, match_confirmation_id):
    accepted_key = f"match:{match_confirmation_id}:accepted"
    cache.sadd(accepted_key, player_id)
    cache.expire(accepted_key, 30)  # Acceptance window of 30 seconds


def check_all_accepted(match_confirmation_id):
    notified_key = f"match:{match_confirmation_id}:notified"
    accepted_key = f"match:{match_confirmation_id}:accepted"
    return cache.scard(notified_key) == cache.scard(accepted_key)


def determine_non_accepting_lobbies(match_confirmation_id, matched_lobbies_ids):
    accepted_key = f"match:{match_confirmation_id}:accepted"
    lobby_players_key_template = "lobby:{}:players"
    non_accepting_lobbies = []

    accepted_players = cache.smembers(accepted_key)
    for lobby_id in matched_lobbies_ids:
        lobby_players_key = lobby_players_key_template.format(lobby_id)
        lobby_players = cache.smembers(lobby_players_key)
        if not all(player in accepted_players for player in lobby_players):
            non_accepting_lobbies.append(lobby_id)

    return non_accepting_lobbies


def requeue_lobbies(matched_lobbies_ids, non_accepting_lobbies_ids):
    queue_key = "matchmaking_lobby_queue"
    for lobby_id in matched_lobbies_ids:
        if lobby_id not in non_accepting_lobbies_ids:
            cache.rpush(queue_key, str(lobby_id))


def broadcast_match_ready(match_confirmation_id, player_ids):
    channel_layer = get_channel_layer()
    for player_id in player_ids:
        async_to_sync(channel_layer.group_send)(
            f"player_{player_id}",
            {
                "type": "match_ready",
                "message": json.dumps({
                    "match_confirmation_id": match_confirmation_id,
                    "message": "Match found! Please confirm.",
                }),
            }
        )


def finalize_match(match_confirmation_id):
    accepted_key = f"match:{match_confirmation_id}:accepted"
    accepted_player_ids = list(cache.smembers(accepted_key))

    # Use apps.get_model() to dynamically import models
    Match = apps.get_model('scrimgg', 'Match')
    Player = apps.get_model('scrimgg', 'Player')

    match = Match.objects.create()
    for player_id in accepted_player_ids:
        try:
            player = Player.objects.get(id=player_id)
            match.players.add(player)
        except Player.DoesNotExist:
            print(f"Player with ID {player_id} does not exist. Skipping.")

    broadcast_match_ready(match_confirmation_id, accepted_player_ids)

    notified_key = f"match:{match_confirmation_id}:notified"
    cache.delete(notified_key, accepted_key)

