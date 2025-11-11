import asyncio
from valclient.client import Client


async def main():
    client = Client()
    client.activate()

    coregame_match = client.coregame_fetch_match()
    match_id = coregame_match.get("MatchID")

    team_chat_token = client.coregame_fetch_team_chat_muc_token(match_id)
    all_chat_token = client.coregame_fetch_allchat_muc_token(match_id)

    print("=== Coregame Match Info ===")
    print(coregame_match)
    print("\n=== Team Chat MUC Token ===")
    print(team_chat_token)
    print("\n=== All Chat MUC Token ===")
    print(all_chat_token)


if __name__ == "__main__":
    asyncio.run(main())

