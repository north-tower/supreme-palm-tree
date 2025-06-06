import asyncio
import websockets
import json

async def test_connection():
    url = "wss://try-demo-eu.po.market/socket.io/?EIO=4&transport=websocket"
    headers = {
        "Origin": "https://pocketoption.com",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    try:
        print("🔄 [ИНФО] Attempting to connect to WebSocket server...")
        async with websockets.connect(url, additional_headers=headers) as websocket:
            print("✅ [ИНФО] Connected to WebSocket server")

            # Socket.IO v4 handshake
            print("🔄 [ИНФО] Starting Socket.IO handshake")
            
            # Send initial connection message
            await websocket.send("40")
            response = await websocket.recv()
            print(f"📥 [ИНФО] Initial response: {response}")

            # Use the working token
            token = "cZoCQNWriz"
            print(f"\n🔄 [ИНФО] Testing authentication with token: {token}")
            
            # Format the auth message according to Socket.IO v4 protocol
            auth_message = ["auth", {"token": token, "balance": 50000}]
            await websocket.send(f"42{json.dumps(auth_message)}")
            
            # Wait for authentication response
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"📥 [ИНФО] Received: {response}")
                    
                    if isinstance(response, bytes):
                        response = response.decode('utf-8')
                    
                    if response.startswith("2"):
                        # Handle ping
                        await websocket.send("3")
                        continue
                        
                    if "successauth" in response.lower():
                        print("✅ [ИНФО] Authentication successful!")
                        break
                    elif "error" in response.lower():
                        print("⚠️ [ОШИБКА] Authentication failed!")
                        return
                    
            except asyncio.TimeoutError:
                print("⚠️ [ОШИБКА] Timeout waiting for authentication response")
                return

            # If we got here, try to change symbol
            print("\n🔄 [ИНФО] Testing symbol change")
            symbol_message = ["changeSymbol", {"asset": "EURUSD", "period": 1}]
            await websocket.send(f"42{json.dumps(symbol_message)}")
            
            # Wait for symbol change response
            try:
                while True:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    print(f"📥 [ИНФО] Symbol response: {response}")
                    
                    if isinstance(response, bytes):
                        response = response.decode('utf-8')
                    
                    if response.startswith("2"):
                        # Handle ping
                        await websocket.send("3")
                        continue
                        
                    if "history" in response.lower():
                        print("✅ [ИНФО] Successfully received history data!")
                        break
                    elif "error" in response.lower():
                        print("⚠️ [ОШИБКА] Failed to change symbol!")
                        break
                        
            except asyncio.TimeoutError:
                print("⚠️ [ОШИБКА] Timeout waiting for symbol change response")

    except websockets.ConnectionClosed as e:
        print(f"⚠️ [ОШИБКА] Connection closed: {e.reason}")
    except Exception as e:
        print(f"⚠️ [ОШИБКА] Unexpected error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_connection()) 