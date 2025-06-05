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
        websocket = await websockets.connect(url, extra_headers=headers, timeout=10)
        print("Connected to WebSocket server")

        await websocket.send("40")  # Initial connection message

        auth_message = ["auth", {"token": token, "balance": 50000}]
        await websocket.send(f"42{json.dumps(auth_message)}")  # Authentication message

        change_symbol_message = ["changeSymbol", {"asset": asset, "period": 1}]
        await websocket.send(f"42{json.dumps(change_symbol_message)}")  # Change symbol message

        async for message in websocket:
            if isinstance(message, bytes):
                try:
                    decoded_message = json.loads(message.decode('utf-8'))
                    if isinstance(decoded_message, dict):
                        history = decoded_message.get("history", [])

                        if history:
                            history_data = [
                                [entry[0], entry[1]]
                                for entry in history
                                if isinstance(entry, list) and len(entry) == 2
                            ]

                            history_summary = HistorySummary(history_data, time_minutes=period)

                            # Get all indicators
                            results = history_summary.get_all_indicators()
                            await websocket.close()

                            return results, history_data

                except (ValueError, KeyError, TypeError) as e:
                    print(f"Error processing binary message: {e}")

    except websockets.ConnectionClosed as e:
        
        print(f"Connection closed: {e.reason}")
    except asyncio.TimeoutError:
        print("Connection timed out. Unable to connect to WebSocket server.")
    except Exception as e:
        await websocket.close()
        print(f"An unexpected error occurred: {e}")
    finally:
        if websocket and not websocket.closed:
            await websocket.close()
            print("WebSocket connection closed.")

    return None


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
