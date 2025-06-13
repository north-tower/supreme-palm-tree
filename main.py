from telethon import TelegramClient, events, Button, types
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
from CurrencyPairs import CurrencyPairs
from demo_test import fetch_summary
from Visualizer   import  TradingChartPlotter
from Helpers import *
from Analysis import HistorySummary
import tempfile
from language_manager import LanguageManager
import json
    # Callback: Prompt for time selection
from functools import partial

# Initialize language manager
lang_manager = LanguageManager()

class TelegramBotClient:
    def __init__(self):
        print("🔄 [ИНФО] Загрузка переменных окружения из файла .env.")
        load_dotenv()
        self.currency_pairs = CurrencyPairs()
        self.user_messages = {}  # Dictionary to store user messages
        self.user_request_count = {}  # Dictionary to track request count per user

        self.api_id = "26422824"
        self.api_hash = "3c8f82c213fbd41b275b8b921d8ed946"
        self.bot_token ="8129679884:AAGEbC-P6_YFQFzERMiV2UevFx6uXAqSUhs"

        if not all([self.api_id, self.api_hash, self.bot_token]):
            raise ValueError("Отсутствуют переменные окружения: API_ID, API_HASH или BOT_TOKEN")

        self.client = None

    async def connect(self):
        try:
            print("🚀 [ИНФО] Инициализация Telegram клиента для бота.")
            self.client = TelegramClient('bot', self.api_id, self.api_hash)
            await self.client.start(bot_token=self.bot_token)
            print("✅ [ИНФО] Успешное подключение к Telegram.")
        except Exception as e:
            print(f"⚠️ [ОШИБКА] Не удалось подключиться: {e}")

    def generate_buttons(self, pairs, selected_asset):
        buttons = [
            [Button.inline(pair, f"pair:{pair}") for pair in pairs[i:i+2]]
            for i in range(0, len(pairs), 2)
        ]
        return buttons  # Removed the 'show_all' and 'show_less' logic

    async def delete_user_messages(self, user_id):
        """Delete all stored messages for a user except the first one"""
        if user_id in self.user_messages:
            # Skip the first message (index 0) if it exists
            for message in self.user_messages[user_id][1:]:
                try:
                    await message.delete()
                except Exception as e:
                    print(f"⚠️ [ОШИБКА] Не удалось удалить сообщение: {e}")
            # Keep only the first message in the list
            if self.user_messages[user_id]:
                self.user_messages[user_id] = [self.user_messages[user_id][0]]
            else:
                self.user_messages[user_id] = []

    async def store_message(self, user_id, message):
        """Store a message for later deletion"""
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
        self.user_messages[user_id].append(message)

    async def start_bot(self):
        try:
            await self.connect()

            # Define the start command handler
            self.client.add_event_handler(self.handle_start_command, events.NewMessage(pattern='/start'))

            # Define the asset selection handler
            self.client.add_event_handler(self.handle_asset_selection, events.CallbackQuery)

            await self.client.run_until_disconnected()

        except Exception as e:
            print(f"⚠️ [ОШИБКА] Не удалось запустить бота: {e}")


    # Callback: Handle the '/start' command
    async def handle_start_command(self, event):
        await self.show_main_menu(event)


    # Callback: Handle asset selection
    async def handle_asset_selection(self, event):
        selected_asset = event.data.decode('utf-8')
        user_id = event.sender_id

        # Initialize request count for new users
        if user_id not in self.user_request_count:
            self.user_request_count[user_id] = 0

        # Increment request count
        self.user_request_count[user_id] += 1

        try:
            if selected_asset == "change_language":
                await self.show_language_selection(event)
            elif selected_asset in ["otc", "regular_assets"]:
                # Only delete messages if this is not the first request
                if self.user_request_count[user_id] > 1:
                    await self.delete_user_messages(user_id)
                await self.display_currency_pairs(event, selected_asset)
            elif selected_asset.startswith("pair:"):
                selected_pair = selected_asset.split(":")[1]
                await self.prompt_for_time(event, selected_pair)
            elif selected_asset.startswith("lang:"):
                new_language = selected_asset.split(":")[1]
                if lang_manager.set_language(new_language):
                    await event.respond(lang_manager.get_text("language_changed"))
                await self.show_main_menu(event)
        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка в handle_asset_selection: {e}")
            # If there's an error, try to show the main menu as a fallback
            try:
                await self.show_main_menu(event)
            except Exception as menu_error:
                print(f"⚠️ [ОШИБКА] Не удалось показать главное меню: {menu_error}")


    # Method: Display currency pairs
    async def display_currency_pairs(self, event, asset_type):
        try:
            pairs = await self.currency_pairs.fetch_pairs(asset_type)
            buttons = self.generate_buttons(pairs, asset_type)

            # Try to edit the message first
            try:
                message = await event.edit(
                    f"🔮💹 *Пожалуйста, выберите валютную пару:* 💹🔮",
                    buttons=buttons
                )
            except Exception as edit_error:
                # If edit fails, send a new message
                print(f"⚠️ [ИНФО] Не удалось отредактировать сообщение, отправляем новое: {edit_error}")
                message = await event.respond(
                    f"🔮💹 *Пожалуйста, выберите валютную пару:* 💹🔮",
                    buttons=buttons
                )
            
            await self.store_message(event.sender_id, message)
        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка в display_currency_pairs: {e}")
            # Try to show main menu as fallback
            await self.show_main_menu(event)

    # Callback: Prompt for time selection
    async def prompt_for_time(self, event, selected_pair):
        try:
            message = await event.respond(
                f"{lang_manager.get_text('select_time')}\n\n"
                f"{lang_manager.get_text('selected_pair')} {selected_pair}\n\n"
                f"{lang_manager.get_text('expiration_time')}",
                buttons=[
                    [Button.inline(lang_manager.get_text("time_1min"), b"1")],
                    [Button.inline(lang_manager.get_text("time_3min"), b"3")],
                    [Button.inline(lang_manager.get_text("time_5min"), b"5")],
                    [Button.inline(lang_manager.get_text("time_15min"), b"15")]
                ]
            )
            await self.store_message(event.sender_id, message)

            # Define a closure for the callback
            async def handle_time_input(response):
                if response.data.decode('utf-8') in ["1", "3", "5", "15"]:
                    # Remove the handler immediately to avoid conflicts
                    self.client.remove_event_handler(handle_time_input, events.CallbackQuery)
                    await self._handle_time_input(response, selected_pair)
                else:
                    await response.answer(lang_manager.get_text("invalid_time"), alert=True)

            # Add the handler with specific data to scope its action
            self.client.add_event_handler(
                handle_time_input,
                events.CallbackQuery(func=lambda e: e.sender_id == event.sender_id)
            )

        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка при запросе времени: {e}")

    # Helper method: Handle time input
    async def _handle_time_input(self, response, selected_pair):
        try:
            time_choice = int(response.data.decode('utf-8'))
            print(f"✅ [ИНФО] Время выбрано: {time_choice} минут для пары {selected_pair}")

            # Process the selection
            await self.process_selection(response, selected_pair, time_choice)

        except ValueError as ve:
            print(f"⚠️ [ОШИБКА] Неверный ввод времени: {ve}")
        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка в процессе обработки выбора: {e}")

    async def process_selection(self, response, selected_pair, time_choice):
        try:
            # Update time mapping to match the `time_choice` values
            time_mapping = {
                1: lang_manager.get_text("time_1min"),
                3: lang_manager.get_text("time_3min"),
                5: lang_manager.get_text("time_5min"),
                15: lang_manager.get_text("time_15min")
            }

            # Clean up the currency pair
            cleaned_pair = remove_country_flags(selected_pair)
            asset = "_".join(cleaned_pair.replace("/", "").split())

            # Replace "OTC" with "_otc" if present
            if asset.endswith("OTC"):
                asset = asset[:-3] + "_otc"

            period = time_choice
            token = "cZoCQNWriz"  # Using the working token

            # Notify the user about the process
            processing_msg = await response.respond(
                lang_manager.get_text("processing_request").format(
                    pair=selected_pair,
                    time=time_mapping[time_choice]
                )
            )
            await self.store_message(response.sender_id, processing_msg)

            # Call fetch_summary with error handling
            results, history_data = await self.fetch_summary_with_handling(asset, period, token)

            if results is None or history_data is None:
                error_msg = await response.respond(lang_manager.get_text("failed_to_get_data"))
                await self.store_message(response.sender_id, error_msg)
                return

            if results and history_data:
                history_summary = HistorySummary(history_data, time_choice)
                signal_info = history_summary.generate_signal(selected_pair, time_choice)

                # Extract signal information
                support = None
                resistance = None
                direction = lang_manager.get_text('buy_signal')

                # Check if signal_info is a string (pre-formatted message)
                if isinstance(signal_info, str):
                    # Extract support and resistance from the pre-formatted message
                    import re
                    # Updated patterns to match the Russian format with asterisks
                    support_match = re.search(r'\*\*Уровень поддержки:\*\*\s*(\d+\.\d+)', signal_info)
                    resistance_match = re.search(r'\*\*Уровень сопротивления:\*\*\s*(\d+\.\d+)', signal_info)
                    direction_match = re.search(r'\*\*Сигнал:\*\*\s*🟥\s*ПРОДАТЬ|\*\*Сигнал:\*\*\s*🟩\s*КУПИТЬ', signal_info)
                    
                    if support_match:
                        support = support_match.group(1)
                    if resistance_match:
                        resistance = resistance_match.group(1)
                    if direction_match:
                        if 'ПРОДАТЬ' in direction_match.group(0):
                            direction = lang_manager.get_text('sell_signal')
                        else:
                            direction = lang_manager.get_text('buy_signal')
                else:
                    # Handle dictionary format
                    if isinstance(signal_info, dict):
                        if 'indicators' in signal_info:
                            indicators = signal_info['indicators']
                            if 'Support and Resistance' in indicators:
                                sr_levels = indicators['Support and Resistance']
                                if isinstance(sr_levels, dict):
                                    support = sr_levels.get('Support')
                                    resistance = sr_levels.get('Resistance')
                        
                        if 'direction' in signal_info:
                            if signal_info['direction'] == 'SELL':
                                direction = lang_manager.get_text('sell_signal')
                            elif signal_info['direction'] == 'NO_SIGNAL':
                                direction = lang_manager.get_text('no_signal')

                # Format the signal response using language manager
                signal_response = lang_manager.get_text('signal_analysis').format(
                    pair=selected_pair,
                    direction=direction,
                    support=support if support is not None else 'N/A',
                    resistance=resistance if resistance is not None else 'N/A'
                )

                # Generate the chart
                chart_plotter = TradingChartPlotter(history_data, selected_pair, time_mapping[time_choice])
                chart_image = chart_plotter.plot_trading_chart()

                if chart_image:
                    # Save the image as a temporary PNG file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                        temp_file_path = temp_file.name
                        temp_file.write(chart_image.read())

                    # Send the chart image as a photo
                    chart_msg = await self.client.send_file(
                        response.sender_id,
                        temp_file_path,
                        force_document=False
                    )
                    await self.store_message(response.sender_id, chart_msg)
                    
                    signal_msg = await response.respond(signal_response)
                    await self.store_message(response.sender_id, signal_msg)

                    # Clean up the temporary file
                    os.remove(temp_file_path)
                else:
                    error_msg = await response.respond(lang_manager.get_text("failed_to_generate_chart"))
                    await self.store_message(response.sender_id, error_msg)
                    
                    signal_msg = await response.respond(signal_response)
                    await self.store_message(response.sender_id, signal_msg)

            else:
                error_msg = await response.respond(
                    lang_manager.get_text("failed_to_get_results").format(asset=asset)
                )
                await self.store_message(response.sender_id, error_msg)

        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка в процессе обработки выбора: {e}")
            error_msg = await response.respond(lang_manager.get_text("error_unknown"))
            await self.store_message(response.sender_id, error_msg)
            
        # Show the main menu after processing
        await self.show_main_menu(response)
   

    async def show_main_menu(self, event):
        print(f"📲 [ИНФО] Отображение главного меню для пользователя {event.sender_id}")
        message = await event.respond(
            lang_manager.get_text("welcome") + "\n\n" +
            "⚠️ *" + lang_manager.get_text("important") + "*\n\n" +
            "💡 " + lang_manager.get_text("lets_start"),
            buttons=[
                [Button.inline("1️⃣ " + lang_manager.get_text("otc_assets"), b"otc")],
                [Button.inline("2️⃣ " + lang_manager.get_text("regular_assets"), b"regular_assets")],
                [Button.inline("🌐 " + lang_manager.get_text("change_language"), b"change_language")]
            ]
        )
        await self.store_message(event.sender_id, message)

    async def show_language_selection(self, event):
        available_languages = {
            "en": "🇬🇧 English",
            "ru": "🇷🇺 Русский"
        }
        
        buttons = []
        for lang_code, lang_name in available_languages.items():
            buttons.append([Button.inline(lang_name, f"lang:{lang_code}")])
        
        message = await event.edit(
            lang_manager.get_text("select_language"),
            buttons=buttons
        )
        await self.store_message(event.sender_id, message)

    async def fetch_summary_with_handling(self, asset, period, token):
        try:
            print(f"🔄 [ИНФО] Fetching data for {asset} with period {period}")
            results, history_data = await fetch_summary(asset, period, token)
            
            if results is None or history_data is None:
                print(f"⚠️ [ОШИБКА] Failed to fetch data for {asset}")
                return None, None
            
            return results, history_data
        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка в fetch_summary_with_handling: {str(e)}")
            return None, None

    async def generate_signal(self, asset: str, timeframe: str) -> str:
        """Generate trading signal using the signal generator"""
        try:
            # Get data from the data collector
            data = await self.data_collector.get_data(asset, timeframe)
            if not data:
                return self.lang_manager.get_text("failed_to_get_data")

            # Generate signal
            signal = self.signal_generator.generate_signal(data)
            
            # Format the response using language manager
            response = f"📊 {self.lang_manager.get_text('signal_analysis', pair=asset, time=timeframe)}\n\n"
            response += f"💪 {self.lang_manager.get_text('signal_strength', strength=signal['strength'])}\n"
            response += f"🎯 {self.lang_manager.get_text('signal_confidence', confidence=signal['confidence'])}\n"
            response += f"�� {self.lang_manager.get_text('signal_direction', direction=signal['direction'])}\n"
            response += f"💡 {self.lang_manager.get_text('signal_recommendation', recommendation=signal['recommendation'])}\n\n"
            
            response += f"📊 {self.lang_manager.get_text('signal_indicators')}\n"
            for indicator, value in signal['indicators'].items():
                response += f"• {indicator}: {value}\n"
            
            response += f"\n📝 {self.lang_manager.get_text('signal_summary')}\n"
            response += f"⚠️ {self.lang_manager.get_text('signal_risk', risk=signal['risk'])}\n"
            response += f"🎯 {self.lang_manager.get_text('signal_entry', entry=signal['entry'])}\n"
            response += f"🚪 {self.lang_manager.get_text('signal_exit', exit=signal['exit'])}\n"
            response += f"🛑 {self.lang_manager.get_text('signal_stop_loss', sl=signal['stop_loss'])}\n"
            response += f"💰 {self.lang_manager.get_text('signal_take_profit', tp=signal['take_profit'])}\n"
            
            return response

        except Exception as e:
            logger.error(f"Error generating signal: {str(e)}")
            return self.lang_manager.get_text("error_unknown")

    async def handle_time_input(self, message: types.Message, asset: str, timeframe: str):
        """Handle time input and generate signal"""
        try:
            # Send processing message
            processing_msg = await message.answer(
                self.lang_manager.get_text("processing_request", pair=asset, time=timeframe)
            )
            
            # Generate signal
            signal = await self.generate_signal(asset, timeframe)
            
            # Send signal
            await message.answer(signal)
            
            # Delete processing message
            await processing_msg.delete()
            
        except Exception as e:
            logger.error(f"Error handling time input: {str(e)}")
            await message.answer(self.lang_manager.get_text("error_unknown"))


if __name__ == "__main__":
    bot_client = TelegramBotClient()
    asyncio.run(bot_client.start_bot())



# from telethon import TelegramClient, events, Button
# import os
# from dotenv import load_dotenv
# import asyncio
# from datetime import datetime
# from CurrencyPairs import CurrencyPairs
# from demo_test import fetch_summary
# from Helpers import *

# class TelegramBotClient:
#     def __init__(self):
#         print("🔄 [INFO] Loading environment variables from .env file.")
#         load_dotenv()
#         self.currency_pairs = CurrencyPairs()

#         self.api_id = os.getenv('API_ID')
#         self.api_hash = os.getenv('API_HASH')
#         self.bot_token = os.getenv('BOT_TOKEN')

#         if not all([self.api_id, self.api_hash, self.bot_token]):
#             raise ValueError("Missing environment variables: API_ID, API_HASH, or BOT_TOKEN")

#         self.client = None

#     async def connect(self):
#         try:
#             print("🚀 [INFO] Initializing Telegram Client for the bot.")
#             self.client = TelegramClient('bot', self.api_id, self.api_hash)
#             await self.client.start(bot_token=self.bot_token)
#             print("✅ [INFO] Successfully connected to Telegram.")
#         except Exception as e:
#             print(f"⚠️ [ERROR] Failed to connect: {e}")

#     def generate_buttons(self, pairs, show_all, selected_asset):
#         buttons = [
#             [Button.inline(pair, f"pair:{pair}") for pair in pairs[i:i+2]]
#             for i in range(0, len(pairs), 2)
#         ]
#         if show_all:
#             buttons.append([Button.inline("See All", f"show_all:{selected_asset}")])
#         else:
#             buttons.append([Button.inline("See Less", f"show_less:{selected_asset}")])
#         return buttons

#     async def start_bot(self):
#         try:
#             await self.connect()

#             @self.client.on(events.NewMessage(pattern='/start'))
#             async def start_command(event):
#                 await self.show_main_menu(event)

#             @self.client.on(events.CallbackQuery)
#             async def asset_selection(event):
#                 selected_asset = event.data.decode('utf-8')

#                 if selected_asset in ["otc", "regular_assets"]:
#                     pairs = await self.currency_pairs.fetch_pairs(selected_asset)
#                     visible_pairs = pairs[:6]
#                     show_all = len(pairs) > 6

#                     buttons = self.generate_buttons(visible_pairs, show_all, selected_asset)

#                     await event.edit(
#                         f"Here are the {selected_asset.replace('_', ' ').capitalize()} Currency Pairs:",
#                         buttons=buttons
#                     )
#                 elif selected_asset.startswith("pair:"):
#                     selected_pair = selected_asset.split(":")[1]
#                     await self.prompt_for_time(event, selected_pair)
#                 elif selected_asset.startswith("show_all:"):
#                     asset_type = selected_asset.split(":")[1]
#                     pairs = await self.currency_pairs.fetch_pairs(asset_type)
#                     buttons = self.generate_buttons(pairs, False, asset_type)

#                     await event.edit(
#                         f"Here are all the {asset_type.replace('_', ' ').capitalize()} Currency Pairs:",
#                         buttons=buttons
#                     )
#                 elif selected_asset.startswith("show_less:"):
#                     asset_type = selected_asset.split(":")[1]
#                     pairs = await self.currency_pairs.fetch_pairs(asset_type)
#                     visible_pairs = pairs[:6]
#                     buttons = self.generate_buttons(visible_pairs, True, asset_type)

#                     await event.edit(
#                         f"Here are the {asset_type.replace('_', ' ').capitalize()} Currency Pairs:",
#                         buttons=buttons
#                     )
#                 else:
#                     await event.respond("⚠️ Invalid option selected.")

#             await self.client.run_until_disconnected()

#         except Exception as e:
#             print(f"⚠️ [ERROR] Failed to start bot: {e}")

#     async def prompt_for_time(self, event, selected_pair):
#         try:
#             await event.respond(
#                 f"✅ You selected: {selected_pair}\n\n⏳ Select expiration time:\n1️⃣ 1 minute\n2️⃣ 3 minutes\n3️⃣ 5 minutes\n4️⃣ 15 minutes"
#             )

#             @self.client.on(events.NewMessage(from_users=event.sender_id))
#             async def handle_time_input(response):
#                 try:
#                     time_choice = int(response.text)
#                     if time_choice not in [1, 2, 3, 4]:
#                         raise ValueError

#                     self.client.remove_event_handler(handle_time_input)

#                     # Pass selected pair and time to a separate function
#                     await self.process_selection(response, selected_pair, time_choice)

#                 except ValueError:
#                     await response.respond("❌ Invalid input. Please enter a number between 1 and 4.")
#                 except Exception as e:
#                     print(f"⚠️ [ERROR] Error in handle_time_input: {e}")

#         except Exception as e:
#             print(f"⚠️ [ERROR] Error in prompting for time: {e}")

#     async def process_selection(self, response, selected_pair, time_choice):
#         """
#         Process the selected currency pair and expiration time.
#         """
#         try:
#             time_mapping = {
#                 1: "1 minute",
#                 2: "3 minutes",
#                 3: "5 minutes",
#                 4: "15 minutes"
#             }

#             # Clean the currency pair (remove emojis, '/', spaces, and replace with '_')
#             cleaned_pair = remove_country_flags(selected_pair)
#             asset = "_".join(cleaned_pair.replace("/", "").split())

#             # Replace trailing "OTC" with "_otc" if it exists
#             if asset.endswith("OTC"):
#                 asset = asset[:-3] + "_otc"  # Remove "OTC" and append "_otc"

#             period = time_choice  # Use the selected time directly as period
#             token = "cZoCQNWriz"  # Replace with the actual token

#             # Inform the user that their request is being processed
#             await response.respond(
#                 f"⏳ Processing your request for {selected_pair} with an expiration time of {time_mapping[time_choice]}...\n"
#                 "Please wait while we fetch the results."
#             )

#             # Call fetch_summary with proper async handling
#             results = await self.fetch_summary_with_handling(asset, period, token)

#             # Respond with the final selection and results
#             if results:
#                 summary = format_summary(results['Summary'])
#                 indicators = format_indicators(results['Indicators'])

#                 await response.respond(
#                     f"🎉 You chose {selected_pair} with an expiration time of {time_mapping[time_choice]}!\n\n"
#                     f"{summary}\n\n{indicators}"
#                 )
#             else:
#                 await response.respond(
#                     f"⚠️ No results were returned for {asset} with the selected time."
#                 )

#         except Exception as e:
#             print(f"⚠️ [ERROR] Error in process_selection: {e}")
#         # Show main menu after processing
#         await self.show_main_menu(response)

#     async def show_main_menu(self, event):
#         print(f"📲 [INFO] Showing main menu to user {event.sender_id}")
#         await event.respond(
#             "🎉 Welcome to the Pocket Option Trading Bot!\n\n💹 Let's start by selecting the type of assets.",
#             buttons=[
#                 [Button.inline("🔹 OTC", b"otc")],
#                 [Button.inline("🔹 Regular Assets", b"regular_assets")]
#             ]
#         )
#     async def fetch_summary_with_handling(self, asset, period, token):
#         """
#         Wrapper for fetch_summary to ensure proper handling for websockets.
#         """
#         try:
#             results = await fetch_summary(asset, period, token)

#             # Add logic to validate the results or reattempt fetching if needed
#             if results:
#                 return results
#             else:
#                 print("⚠️ [WARNING] No results fetched. Reattempting may be required.")
#                 return None

#         except Exception as e:
#             print(f"⚠️ [ERROR] Error in fetch_summary_with_handling: {e}")
#             return None

# if __name__ == "__main__":
#     bot_client = TelegramBotClient()
#     asyncio.run(bot_client.start_bot())

