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
        print(f"🔄 [ИНФО] Connecting to WebSocket server for {asset}")
        async with websockets.connect(url, additional_headers=headers) as websocket:
            print("✅ [ИНФО] Connected to WebSocket server")

            # Socket.IO v4 handshake
            print("🔄 [ИНФО] Starting Socket.IO handshake")
            await websocket.send("40")
            response = await websocket.recv()
            print(f"📥 [ИНФО] Initial response: {response}")

            # Authentication
            print("🔄 [ИНФО] Authenticating...")
            auth_message = ["auth", {"token": token, "balance": 50000}]
            await websocket.send(f"42{json.dumps(auth_message)}")
            
            # Wait for authentication
            while True:
                response = await websocket.recv()
                if isinstance(response, bytes):
                    response = response.decode('utf-8')
                print(f"📥 [ИНФО] Auth response: {response}")
                
                if "successauth" in response.lower():
                    print("✅ [ИНФО] Authentication successful!")
                    break
                elif "error" in response.lower():
                    print("⚠️ [ОШИБКА] Authentication failed!")
                    return None, None

            # Change symbol
            print(f"🔄 [ИНФО] Changing symbol to {asset}")
            symbol_message = ["changeSymbol", {"asset": asset, "period": 1}]
            await websocket.send(f"42{json.dumps(symbol_message)}")
            
            # Wait for history data and collect it
            history_data = []
            data_collection_timeout = 10  # seconds to collect data
            start_time = asyncio.get_event_loop().time()
            
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1)
                    if isinstance(response, bytes):
                        response = response.decode('utf-8')
                    
                    # Handle ping messages
                    if response.startswith("2"):
                        await websocket.send("3")
                        continue
                    
                    # Handle data messages
                    if response.startswith("["):
                        try:
                            data = json.loads(response)
                            if isinstance(data, list) and len(data) > 0:
                                # Check if this is a price data point (should have 3 elements: symbol, timestamp, price)
                                if len(data[0]) == 3 and isinstance(data[0][0], str) and isinstance(data[0][1], (int, float)) and isinstance(data[0][2], (int, float)):
                                    # Only collect data for our target asset
                                    if data[0][0] == asset:
                                        history_data.append(data[0])
                                        print(f"📥 [ИНФО] Received data point for {asset}: {data[0]}")
                        except json.JSONDecodeError:
                            continue
                    
                    # Check if we've collected enough data or timeout
                    if len(history_data) >= 100 or (asyncio.get_event_loop().time() - start_time) > data_collection_timeout:
                        print(f"✅ [ИНФО] Collected {len(history_data)} data points")
                        break
                        
                except asyncio.TimeoutError:
                    # Check if we've collected enough data
                    if len(history_data) >= 100:
                        print(f"✅ [ИНФО] Collected {len(history_data)} data points")
                        break
                    continue

            if history_data:
                print(f"✅ [ИНФО] Processing {len(history_data)} data points")
                # Convert the data to the format expected by HistorySummary
                formatted_data = [[point[1], point[2]] for point in history_data]  # [timestamp, price]
                history_summary = HistorySummary(formatted_data, time_minutes=period)
                results = history_summary.get_all_indicators()
                return results, formatted_data
            else:
                print("⚠️ [ОШИБКА] No history data collected")
                return None, None

    except websockets.ConnectionClosed as e:
        print(f"⚠️ [ОШИБКА] Connection closed: {e.reason}")
    except Exception as e:
        print(f"⚠️ [ОШИБКА] Unexpected error: {str(e)}")
    
    return None, None


async def main():
    # Define the parameters
    asset = "AUDJPY_otc"
    period = 1
    token = "cZoCQNWriz"

    # Call the fetch_summary function to get the results
    results, history_data = await fetch_summary(asset, period, token)
    signal_gen = SignalGenerator(history_data)
    signal = signal_gen.generate_signal()

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
