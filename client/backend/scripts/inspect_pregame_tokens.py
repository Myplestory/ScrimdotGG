import asyncio
from valclient.client import Client


async def main():
    client = Client()
    client.activate()

    match_info = client.pregame_fetch_match()
    match_id = match_info.get("MatchID")

    chat_token = client.pregame_fetch_chat_token(match_id)
    voice_token = client.pregame_fetch_voice_token(match_id)

    print("=== Pregame Match Info ===")
    print(match_info)
    print("\n=== Pregame Chat Token ===")
    print(chat_token)
    print("\n=== Pregame Voice Token ===")
    print(voice_token)


if __name__ == "__main__":
    asyncio.run(main())

