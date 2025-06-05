from telethon import TelegramClient, events, Button
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
    # Callback: Prompt for time selection
from functools import partial


class TelegramBotClient:
    def __init__(self):
        print("🔄 [ИНФО] Загрузка переменных окружения из файла .env.")
        load_dotenv()
        self.currency_pairs = CurrencyPairs()

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

        if selected_asset in ["otc", "regular_assets"]:
            # Always show all pairs by default
            await self.display_currency_pairs(event, selected_asset)
        elif selected_asset.startswith("pair:"):
            selected_pair = selected_asset.split(":")[1]
            await self.prompt_for_time(event, selected_pair)


    # Method: Display currency pairs
    async def display_currency_pairs(self, event, asset_type):
        pairs = await self.currency_pairs.fetch_pairs(asset_type)
        buttons = self.generate_buttons(pairs, asset_type)

        await event.edit(
            f"🔮💹 *Пожалуйста, выберите валютную пару:* 💹🔮",
            buttons=buttons
        )

    # Callback: Prompt for time selection
    async def prompt_for_time(self, event, selected_pair):
        try:
            await event.respond(
                f"💡 *Выберите подходящее время для начала магии!* 🔮\n\n✅ Вы выбрали: {selected_pair}\n\n⏳✨ *Укажите время истечения:* ✨⏳",
                buttons=[
                    [Button.inline("1️⃣ 1 минута 🕐", b"1")],
                    [Button.inline("3️⃣ 3 минуты 🕒", b"3")],
                    [Button.inline("5️⃣ 5 минут 🕔", b"5")],
                    [Button.inline("1️⃣5️⃣ 15 минут 🕘", b"15")]
                ]
            )

            # Define a closure for the callback
            async def handle_time_input(response):
                if response.data.decode('utf-8') in ["1", "3", "5", "15"]:
                    # Remove the handler immediately to avoid conflicts
                    self.client.remove_event_handler(handle_time_input, events.CallbackQuery)
                    await self._handle_time_input(response, selected_pair)
                else:
                    await response.answer("⚠️ Неверный выбор времени.", alert=True)

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
        """
        Обработать выбранную валютную пару и время истечения.
        """
        try:
            # Update time mapping to match the `time_choice` values
            time_mapping = {
                1: "1 минута",
                3: "3 минуты",
                5: "5 минут",
                15: "15 минут"
            }

            # Clean up the currency pair
            cleaned_pair = remove_country_flags(selected_pair)
            asset = "_".join(cleaned_pair.replace("/", "").split())

            # Replace "OTC" with "_otc" if present
            if asset.endswith("OTC"):
                asset = asset[:-3] + "_otc"

            period = time_choice
            token ="_p_9FptVKA"

            # Notify the user about the process
            await response.respond(
                f"⏳ Обработка запроса для {selected_pair} с временем истечения {time_mapping[time_choice]}...\n"
                "Пожалуйста, подождите, пока мы получим результаты."
            )

            # Call fetch_summary with error handling
            results, history_data = await self.fetch_summary_with_handling(asset, period, token)

            if results and history_data:
                # Format results (optional)
                # summary = format_summary(results['Summary'])
                # indicators = format_indicators(results['Indicators'])
                history_summary = HistorySummary(history_data, time_choice)
                signal_info = history_summary.generate_signal(selected_pair, time_choice)

                # Generate the chart
                chart_plotter = TradingChartPlotter(history_data, selected_pair, time_mapping[time_choice])
                chart_image = chart_plotter.plot_trading_chart()

                if chart_image:
                    # Save the image as a temporary PNG file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                        temp_file_path = temp_file.name
                        temp_file.write(chart_image.read())  # Write the BytesIO content to the temporary file

                    # Send the chart image as a photo (inline image)
                    await self.client.send_file(
                        response.sender_id,
                        temp_file_path,  # Sending the temporary PNG file
                        
                        force_document=False  # Tells Telethon to send it as a photo
                    )
                    await response.respond(
                        f"{signal_info}"
                    )

                    # Clean up the temporary file after sending
                    os.remove(temp_file_path)
                else:
                    await response.respond(
                        "⚠️ Не удалось сгенерировать график, но ниже приведены резюме и индикаторы."
                    )
                    await response.respond(
                        f"🎉 Вы выбрали {selected_pair} с временем истечения {time_mapping[time_choice]}!\n\n"
                        f"{signal_info}"
                    )

            else:
                await response.respond(
                    f"⚠️ Не удалось получить результаты для {asset} с выбранным временем истечения."
                )

        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка в процессе обработки выбора: {e}")
        # Show the main menu after processing
        await self.show_main_menu(response)
   

    async def show_main_menu(self, event):
        print(f"📲 [ИНФО] Отображение главного меню для пользователя {event.sender_id}")
        await event.respond(
            "✨🔮 Добро пожаловать в бота \"Мистический трейдер\"! 🔮✨\n"
            "🧙‍♂️ Здесь вы откроете для себя магию сигналов и таинственные знаки рынка. 📈📉\n\n"
            "⚠️ *Важно:* Это не кнопка для легких денег! Помните о риск-менеджменте 💰 и дисциплине 📊.\n\n"
            "💡 Давайте начнем! Выберите:\n"
            "1️⃣ OTC-активы\n"
            "2️⃣ Обычные валютные пары",
            buttons=[
                [Button.inline("1️⃣ OTC-активы 🔄 (доступны 24/7)", b"otc")],
                [Button.inline("2️⃣ Обычные активы 🌐 (во время работы рынков)", b"regular_assets")]
            ]
        )


    async def fetch_summary_with_handling(self, asset, period, token):
        """
        Обертка для fetch_summary для обработки с использованием WebSocket.
        """
        try:
            results, history_data = await fetch_summary(asset, period, token)

            if results:
                return results, history_data
            else:
                print("⚠️ [ПРЕДУПРЕЖДЕНИЕ] Результаты не получены. Может потребоваться повторная попытка.")
                return None, None

        except Exception as e:
            print(f"⚠️ [ОШИБКА] Ошибка в fetch_summary_with_handling: {e}")
            return None, None


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
#             "🎉 Welcome to the Pocket Option Trading Bot!\n\n💹 Let’s start by selecting the type of assets.",
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

