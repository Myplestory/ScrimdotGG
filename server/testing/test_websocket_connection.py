"""
Test WebSocket connection to Django server
"""
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/52f0666e-4d7a-5b84-9e1a-a35286de3d27"
    
    try:
        async with websockets.connect(uri) as websocket:
            print("✅ Connected to Django WebSocket")
            
            # Test lobby creation
            message = {
                "event": "create_lobby",
                "payload": {
                    "puuid": "52f0666e-4d7a-5b84-9e1a-a35286de3d27"
                }
            }
            
            print(f"📤 Sending: {message}")
            await websocket.send(json.dumps(message))
            
            # Wait for response
            response = await websocket.recv()
            print(f"📥 Received: {response}")
            
            # Test queue join
            message2 = {
                "event": "add_lobby_to_queue",
                "payload": {
                    "lobby_id": "655d1c06-288e-42cf-86dd-1543d85ed233",
                    "requester_puuid": "52f0666e-4d7a-5b84-9e1a-a35286de3d27",
                    "queue_type": "pug"
                }
            }
            
            print(f"📤 Sending: {message2}")
            await websocket.send(json.dumps(message2))
            
            # Wait for response
            response2 = await websocket.recv()
            print(f"📥 Received: {response2}")
            
    except Exception as e:
        print(f"❌ WebSocket error: {e}")

if __name__ == "__main__":
    asyncio.run(test_websocket())
