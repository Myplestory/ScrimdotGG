from rest_framework import serializers
from scrimgg.models import Player, Lobby, Match

class PlayerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Player
        fields = '__all__' 
        

class LobbySerializer(serializers.ModelSerializer):
    players = PlayerSerializer(many=True, read_only=True)
    lobby_leader = PlayerSerializer(read_only=True)
    class Meta:
        model = Lobby
        fields = '__all__'
        
class MatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Match
        fields = '__all__'