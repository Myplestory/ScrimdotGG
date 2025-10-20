# Match Page (Client - Backend)

Comprehensive client backend documentation for constructor and join flows.

## Constructor Flow
```python
async def create_custom_game_for_match(self, match_id: str, map_name: str, server: str, starting_side: str):
    custom_response = self.client.party_change_to_custom()
    pregame_id = custom_response.get('ID')
    if not pregame_id:
        raise ValueError("Failed to create custom game")
    build_args = {
        "Map": self.args['mapPreferences'][map_name],
        "Mode": "/Game/GameModes/Bomb/BombGameMode.BombGameMode_C",
        "GamePod": self._get_server_url(server),
        "UseBots": False,
        "GameRules": {
            "AllowGameModifiers": "true",
            "PlayOutAllRounds": "true",
            "SkipMatchHistory": "true",
            "TournamentMode": "false",
            "IsOvertimeWinByTwo": "true",
        },
    }
    self.client.party_set_custom_game_settings(build_args)
    await self.pugsocket.send_message('custom_game_created', {
        'match_id': match_id,
        'pregame_id': pregame_id,
        'constructor_puuid': self.client.puuid
    })
```

## Join Flow
```python
async def join_custom_game(self, pregame_id: str, match_id: str):
    try:
        try:
            current_party = self.client.party_fetch_player()
            if current_party:
                self.client.party_leave(current_party['CurrentPartyID'])
        except:
            pass
        result = self.client.party_join(pregame_id)
        await self.pugsocket.send_message('player_joined_pregame', {
            'match_id': match_id,
            'player_puuid': self.client.puuid,
            'success': True
        })
        return {'status': 'success'}
    except Exception as e:
        await self.pugsocket.send_message('player_joined_pregame', {
            'match_id': match_id,
            'player_puuid': self.client.puuid,
            'success': False,
            'error': str(e)
        })
        return {'status': 'error', 'message': str(e)}
```

## Retry Logic
```python
async def rejoin_custom_game_with_retry(self, pregame_id: str, match_id: str, max_retries=3):
    for attempt in range(max_retries):
        try:
            result = await self.join_custom_game(pregame_id, match_id)
            if result['status'] == 'success':
                return result
            await asyncio.sleep(2 ** attempt)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            await asyncio.sleep(2 ** attempt)
    raise Exception("Failed to join custom game after multiple attempts")
```
