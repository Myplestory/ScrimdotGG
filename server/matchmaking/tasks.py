from trueskill import rate, Rating, quality_1vs1
from celery import shared_task
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import Lobby, Match
from .matchmaking import (get_matchmaking_queue,
                          calculate_lobby_trueskill, initiate_match_confirmation, check_all_accepted, finalize_match)
from server.scrimgg.matchmaking.matchconfirm import determine_non_accepting_lobbies, requeue_lobbies, cleanup_match_confirmation, broadcast_match_ready
import json

@shared_task
def process_matchmaking_queue():
    # Get the redis sorted set
    queue = get_matchmaking_queue(sorted=True)
    matched_lobbies = []
    # While queue populated perform search
    while len(queue) >= 2:
        best_match_quality = 0
        best_match = None
        for i in range(len(queue)):
            for j in range(i + 1, len(queue)):
                lobby1 = queue[i]
                lobby2 = queue[j]
                match_quality = quality_1vs1(calculate_lobby_trueskill(lobby1), calculate_lobby_trueskill(lobby2))
                if match_quality > best_match_quality:
                    best_match_quality = match_quality
                    best_match = (i, j)
        # Found a potential match, begin notifying participants
        if best_match is not None:
            i, j = best_match
            lobby1, lobby2 = queue[i], queue[j]
            matched_players = [player for lobby in [lobby1, lobby2] for player in lobby.players.all()]
            matched_players_ids = [player.id for player in matched_players]  
            # Extract player IDs
            match_confirmation_id = initiate_match_confirmation(matched_players_ids)
            broadcast_match_ready(match_confirmation_id, matched_players)
            # Schedule the task to check for all acceptances after a delay
            check_and_finalize_match.apply_async(args=[match_confirmation_id, matched_players_ids], countdown=30)
            # Remove the matched lobbies from the queue
            queue = [lobby for idx, lobby in enumerate(queue) if idx not in [i, j]]
    return matched_lobbies

@shared_task
# Task to check if all accepted, upon which it creates and publishes the match object
def check_and_finalize_match(match_confirmation_id, matched_players_ids, matched_lobbies_ids):
    if check_all_accepted(match_confirmation_id):
        finalize_match(match_confirmation_id, matched_players_ids)
    else:
        # Identify non-accepting lobbies
        non_accepting_lobbies = determine_non_accepting_lobbies(match_confirmation_id, matched_lobbies_ids)
        # Requeue accepting lobbies
        requeue_lobbies(matched_lobbies_ids, non_accepting_lobbies)
        # Cleanup Redis data
        cleanup_match_confirmation(match_confirmation_id)