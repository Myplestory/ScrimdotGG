from django.core.cache import cache
from django_redis import get_redis_connection
from scrimgg.models import Lobby
import trueskill

QUEUE_KEY = 'matchmaking_lobby_queue'

def add_lobby_to_queue(lobby_id, lobby_rating):
    """
    Adds a lobby to the Redis sorted set with its rating as the score.
    """
    redis_conn = get_redis_connection("default")
    queue_key = 'matchmaking_lobby_queue'
    redis_conn.zadd(queue_key, {lobby_id: lobby_rating})

def remove_lobby_from_queue(lobby_id):
    """
    Removes a lobby from the Redis sorted set.
    """
    redis_conn = get_redis_connection("default")
    redis_conn.zrem(QUEUE_KEY, lobby_id)

def get_matchmaking_queue():
    """
    Retrieves the entire queue from the Redis sorted set.
    """
    redis_conn = get_redis_connection("default")
    return redis_conn.zrange(QUEUE_KEY, 0, -1, withscores=True)

env = trueskill.TrueSkill(draw_probability=0)

def calculate_lobby_rating(lobby):
    """
    Calculates the average rating for a given lobby.
    """
    return sum(player.rating for player in lobby.players.all()) / len(lobby.players.all())  # Access players via ORM

def update_ratings(team1, team2, team1_won):
    """
    Updates TrueSkill ratings based on match outcome.
    """
    team1_ratings = [(player.rating, player.sigma) for player in team1]
    team2_ratings = [(player.rating, player.sigma) for player in team2]
    if team1_won:
        new_ratings = env.rate([team1_ratings, team2_ratings], ranks=[0, 1])
    else:
        new_ratings = env.rate([team1_ratings, team2_ratings], ranks=[1, 0])
    for player, new_rating in zip(team1 + team2, new_ratings[0] + new_ratings[1]):
        player.rating, player.sigma = new_rating
        player.save() 

def get_players_from_lobbies(lobby_ids):
    """
    Retrieves players from the given lobby IDs.
    """
    players = []
    for lobby_id in lobby_ids:
        # Fetch the lobby by its UUID
        lobby = Lobby.objects.get(uuid=lobby_id)  
        players.extend(list(lobby.players.all())) 
    return players