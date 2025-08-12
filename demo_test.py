import asyncio
import json
import pandas as pd
import websockets
from Analysis import HistorySummary
from Visualizer import TradingChartPlotter
from SignalGenerator import SignalGenerator
from Helpers import *

async def fetch_summary(asset, period, token):
    url = "wss://try-demo-eu.po.market/socket.io/?EIO=4&transport=websocket"
    headers = {
        "Origin": "https://pocketoption.com",
        "Cache-Control": "no-cache",
        "Pragma": "no-cache",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    }

    websocket = None
    try:
        print(f"🔄 [INFO] Connecting to WebSocket server for {asset}")
        async with websockets.connect(url, additional_headers=headers, ping_interval=None, ping_timeout=None) as websocket:
            print("✅ [INFO] Connected to WebSocket server")

            # Socket.IO v4 handshake
            print("🔄 [INFO] Starting Socket.IO handshake")
            await websocket.send("40")
            response = await websocket.recv()
            print(f"📥 [INFO] Initial response: {response}")

            # Authentication
            print("🔄 [INFO] Authenticating...")
            auth_message = ["auth", {"token": token, "balance": 50000}]
            await websocket.send(f"42{json.dumps(auth_message)}")
            
            # Wait for authentication with better error handling
            auth_timeout = 15  # increased timeout
            auth_start_time = asyncio.get_event_loop().time()
            auth_success = False
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=3)
                    if isinstance(response, bytes):
                        response = response.decode('utf-8')
                        print(f"📥 [INFO] Auth response: {response}")
                        
                        # Handle ping messages during auth
                        if response.startswith("2"):
                            await websocket.send("3")
                            continue
                        
                        if "successauth" in response.lower() or "auth" in response.lower():
                            print("✅ [INFO] Authentication successful!")
                            auth_success = True
                            break
                        elif "error" in response.lower():
                            print("⚠️ [ERROR] Authentication failed!")
                            return None, None
                        
                        # Check timeout
                        if (asyncio.get_event_loop().time() - auth_start_time) > auth_timeout:
                            print("⚠️ [WARNING] Authentication timeout - proceeding anyway")
                            auth_success = True
                            break
                except asyncio.TimeoutError:
                    print("⚠️ [WARNING] Authentication timeout - proceeding anyway")
                    auth_success = True
                    break
                except websockets.ConnectionClosed:
                    print("⚠️ [ERROR] Connection closed during authentication")
                    return None, None

            if not auth_success:
                print("⚠️ [ERROR] Authentication failed")
                return None, None

            # Change symbol
            print(f"🔄 [INFO] Changing symbol to {asset}")
            symbol_message = ["changeSymbol", {"asset": asset, "period": 1}]
            await websocket.send(f"42{json.dumps(symbol_message)}")
            
            # Wait for symbol change confirmation
            symbol_timeout = 10  # increased timeout
            symbol_start_time = asyncio.get_event_loop().time()
            symbol_success = False
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    if isinstance(response, bytes):
                        response = response.decode('utf-8')
                    
                    # Handle ping messages
                    if response.startswith("2"):
                        await websocket.send("3")
                        continue
                    
                    # Check for symbol change success or any data
                    if response.startswith("[") or "history" in response.lower() or "symbol" in response.lower():
                        print("✅ [INFO] Symbol change successful or data received")
                        symbol_success = True
                        break
                    
                    # Check timeout
                    if (asyncio.get_event_loop().time() - symbol_start_time) > symbol_timeout:
                        print("⚠️ [WARNING] Symbol change timeout - proceeding anyway")
                        symbol_success = True
                        break
                except asyncio.TimeoutError:
                    print("⚠️ [WARNING] Symbol change timeout - proceeding anyway")
                    symbol_success = True
                    break
                except websockets.ConnectionClosed:
                    print("⚠️ [ERROR] Connection closed during symbol change")
                    return None, None

            if not symbol_success:
                print("⚠️ [ERROR] Symbol change failed")
                return None, None
            
            # Wait for history data and collect it
            history_data = []
            data_collection_timeout = 20  # increased timeout
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    if isinstance(response, bytes):
                        response = response.decode('utf-8')
                    
                    # Handle ping messages
                    if response.startswith("2"):
                        await websocket.send("3")
                        continue
                    
                    # Handle data messages - more flexible parsing
                    if response.startswith("[") or response.startswith("{"):
                        try:
                            data = json.loads(response)
                            
                            # Handle array format: [["AUDJPY", timestamp, price], ...]
                            if isinstance(data, list) and len(data) > 0:
                                for item in data:
                                    if isinstance(item, list) and len(item) >= 3:
                                        if item[0] == asset:
                                            history_data.append(item)
                                            print(f"📥 [INFO] Received data point for {asset}: {item}")
                            
                            # Handle object format: {"history": [[timestamp, price], ...]}
                            elif isinstance(data, dict) and "history" in data:
                                history_list = data["history"]
                                if isinstance(history_list, list):
                                    for i, item in enumerate(history_list):
                                        if isinstance(item, list) and len(item) >= 2:
                                            # Add asset name if not present
                                            if len(item) == 2:
                                                item = [asset, item[0], item[1]]
                                            history_data.append(item)
                                            print(f"📥 [INFO] Received history point for {asset}: {item}")
                        except json.JSONDecodeError:
                            continue
                    
                    # Check if we've collected enough data or timeout
                    if len(history_data) >= 50 or (asyncio.get_event_loop().time() - start_time) > data_collection_timeout:
                        print(f"✅ [INFO] Collected {len(history_data)} data points")
                        break
                        
                except asyncio.TimeoutError:
                    # Check if we've collected enough data
                    if len(history_data) >= 10:  # Lower threshold for regular assets
                        print(f"✅ [INFO] Collected {len(history_data)} data points")
                        break
                    continue
                except websockets.ConnectionClosed:
                    print("⚠️ [ERROR] Connection closed during data collection")
                    break

            if history_data:
                print(f"✅ [INFO] Processing {len(history_data)} data points")
                # Convert the data to the format expected by HistorySummary
                formatted_data = [[point[1], point[2]] for point in history_data]  # [timestamp, price]
                history_summary = HistorySummary(formatted_data, time_minutes=period)
                results = history_summary.get_all_indicators()
                return results, formatted_data
            else:
                print("⚠️ [ERROR] No history data collected")
                return None, None

    except websockets.ConnectionClosed as e:
        print(f"⚠️ [ERROR] Connection closed: {e.reason}")
    except Exception as e:
        print(f"⚠️ [ERROR] Unexpected error: {str(e)}")
    
    return None, None


async def main():
    # Define the parameters
    asset = "AUDJPY_otc"
    period = 1
    token = "cZoCQNWriz"

    # Call the fetch_summary function to get the results
    results, history_data = await fetch_summary(asset, period, token)
    signal_gen = SignalGenerator()
    signal = await signal_gen.generate_signal(asset, period)

    print("Generated Signal:", signal)
    print(results)
    chart_plotter = TradingChartPlotter(history_data, asset, "5 mins")

    # Generate and get the chart as image data
    image_data = chart_plotter.plot_trading_chart(outlier_threshold=1.5)

    # Save the image data to a file or use it directly
    if image_data:
        with open("trading_chart.png", "wb") as f:
            f.write(image_data.read())
        print("Chart saved successfully.")
    # # Ensure results exist before proceeding
    # if results:
    #     # Define the currency pair and time period for visualization
    #     currency_pair = f"{asset}"
    #     time_period = f"{period}-minute"

    #     # Create an instance of IndicatorVisualizer
    #     visualizer = IndicatorVisualizer(results, currency_pair, time_period)

    #     # Plot the indicators and save the image
    #     image_data = visualizer.plot_indicators()
    #     if image_data:
    #         with open(f"{currency_pair}_{time_period}_analysis.png", "wb") as image_file:
    #             image_file.write(image_data.read())
    #         print(f"Image saved as {currency_pair}_{time_period}_analysis.png")
    #     else:
    #         print("Failed to generate the image.")
    # else:
    #     print("No results were returned. Unable to visualize indicators.")

if __name__=="__main__":
    # Run the main function
    asyncio.run(main())
