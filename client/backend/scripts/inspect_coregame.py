import asyncio
from valclient.client import Client


async def main():
    client = Client()
    client.activate()
    coregame = client.coregame_fetch_match()
    print(coregame)


if __name__ == "__main__":
    asyncio.run(main())

