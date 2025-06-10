from telethon import TelegramClient, events, Button
import os
from dotenv import load_dotenv
import asyncio
from datetime import datetime
from CurrencyPairs import CurrencyPairs
from demo_test import fetch_summary
from Visualizer import TradingChartPlotter
from Helpers import *
from Analysis import HistorySummary
import tempfile
from languages import LANGUAGES, DEFAULT_LANGUAGE, LANGUAGE_BUTTONS
from functools import partial

class TelegramBotClient:
    def __init__(self):
        print("🔄 [INFO] Loading environment variables from .env file.")
        load_dotenv()
        self.currency_pairs = CurrencyPairs()
        self.user_languages = {}  # Store user language preferences

        self.api_id = "26422824"
        self.api_hash = "3c8f82c213fbd41b275b8b921d8ed946"
        self.bot_token = "8129679884:AAGEbC-P6_YFQFzERMiV2UevFx6uXAqSUhs"

        if not all([self.api_id, self.api_hash, self.bot_token]):
            raise ValueError("Missing environment variables: API_ID, API_HASH, or BOT_TOKEN")

        self.client = None

    def get_user_language(self, user_id):
        """Get user's preferred language or return default"""
        return self.user_languages.get(user_id, DEFAULT_LANGUAGE)

    def get_text(self, user_id, key, **kwargs):
        """Get translated text for the given key"""
        lang = self.get_user_language(user_id)
        text = LANGUAGES[lang][key]
        return text.format(**kwargs) if kwargs else text

    async def connect(self):
        try:
            print("🚀 [INFO] Initializing Telegram Client for the bot.")
            self.client = TelegramClient('bot', self.api_id, self.api_hash)
            await self.client.start(bot_token=self.bot_token)
            print("✅ [INFO] Successfully connected to Telegram.")
        except Exception as e:
            print(f"⚠️ [ERROR] Failed to connect: {e}")

    def generate_buttons(self, pairs, selected_asset, user_id):
        buttons = [
            [Button.inline(pair, f"pair:{pair}") for pair in pairs[i:i+2]]
            for i in range(0, len(pairs), 2)
        ]
        return buttons

    async def start_bot(self):
        try:
            await self.connect()

            # Define the start command handler
            self.client.add_event_handler(self.handle_start_command, events.NewMessage(pattern='/start'))
            # Define the language selection handler
            self.client.add_event_handler(self.handle_language_selection, events.CallbackQuery(pattern='^lang:'))
            # Define the asset selection handler
            self.client.add_event_handler(self.handle_asset_selection, events.CallbackQuery)

            await self.client.run_until_disconnected()

        except Exception as e:
            print(f"⚠️ [ERROR] Failed to start bot: {e}")

    async def handle_start_command(self, event):
        await self.show_language_selection(event)

    async def show_language_selection(self, event):
        """Show language selection menu"""
        buttons = [
            [Button.inline(text, f"lang:{lang}")] 
            for lang, text in LANGUAGE_BUTTONS.items()
        ]
        
        await event.respond(
            "🌍 Please select your language / Por favor, seleccione su idioma / Пожалуйста, выберите ваш язык:",
            buttons=buttons
        )

    async def handle_language_selection(self, event):
        """Handle language selection"""
        lang = event.data.decode('utf-8').split(':')[1]
        user_id = event.sender_id
        self.user_languages[user_id] = lang
        await self.show_main_menu(event)

    async def handle_asset_selection(self, event):
        selected_asset = event.data.decode('utf-8')
        user_id = event.sender_id

        if selected_asset in ["otc", "regular_assets"]:
            await self.display_currency_pairs(event, selected_asset)
        elif selected_asset.startswith("pair:"):
            selected_pair = selected_asset.split(":")[1]
            await self.prompt_for_time(event, selected_pair)

    async def display_currency_pairs(self, event, asset_type):
        user_id = event.sender_id
        pairs = await self.currency_pairs.fetch_pairs(asset_type)
        buttons = self.generate_buttons(pairs, asset_type, user_id)

        await event.edit(
            self.get_text(user_id, 'select_pair'),
            buttons=buttons
        )

    async def prompt_for_time(self, event, selected_pair):
        try:
            user_id = event.sender_id
            lang = self.get_user_language(user_id)
            buttons = [
                [Button.inline(LANGUAGES[lang]['buttons']['time_1'], b"1")],
                [Button.inline(LANGUAGES[lang]['buttons']['time_3'], b"3")],
                [Button.inline(LANGUAGES[lang]['buttons']['time_5'], b"5")],
                [Button.inline(LANGUAGES[lang]['buttons']['time_15'], b"15")]
            ]

            await event.respond(
                self.get_text(user_id, 'select_time', pair=selected_pair),
                buttons=buttons
            )

            async def handle_time_input(response):
                if response.data.decode('utf-8') in ["1", "3", "5", "15"]:
                    self.client.remove_event_handler(handle_time_input, events.CallbackQuery)
                    await self._handle_time_input(response, selected_pair)
                else:
                    await response.answer(self.get_text(user_id, 'error_invalid_time'), alert=True)

            self.client.add_event_handler(
                handle_time_input,
                events.CallbackQuery(func=lambda e: e.sender_id == event.sender_id)
            )

        except Exception as e:
            print(f"⚠️ [ERROR] Error in prompt_for_time: {e}")

    async def _handle_time_input(self, response, selected_pair):
        try:
            time_choice = int(response.data.decode('utf-8'))
            print(f"✅ [INFO] Time selected: {time_choice} minutes for pair {selected_pair}")
            await self.process_selection(response, selected_pair, time_choice)

        except ValueError as ve:
            print(f"⚠️ [ERROR] Invalid time input: {ve}")
        except Exception as e:
            print(f"⚠️ [ERROR] Error in process selection: {e}")

    async def process_selection(self, response, selected_pair, time_choice):
        try:
            user_id = response.sender_id
            lang = self.get_user_language(user_id)
            
            # Delete previous messages
            try:
                chat = await self.client.get_entity(user_id)
                messages = await self.client.get_messages(chat, limit=20)
                
                for message in reversed(messages):
                    try:
                        if message.id != response.message_id:
                            await message.delete()
                            print(f"✅ [INFO] Deleted message {message.id}")
                    except Exception as msg_error:
                        print(f"⚠️ [ERROR] Failed to delete message {message.id}: {msg_error}")
                        continue
                
                print("✅ [INFO] Chat cleanup completed")
            except Exception as e:
                print(f"⚠️ [ERROR] Failed to clean chat: {e}")

            cleaned_pair = remove_country_flags(selected_pair)
            asset = "_".join(cleaned_pair.replace("/", "").split())

            if asset.endswith("OTC"):
                asset = asset[:-3] + "_otc"

            period = time_choice
            token = "cZoCQNWriz"

            await response.respond(
                self.get_text(user_id, 'processing', 
                            pair=selected_pair, 
                            time=LANGUAGES[lang]['time_options'][time_choice])
            )

            results, history_data = await self.fetch_summary_with_handling(asset, period, token)

            if results is None or history_data is None:
                await response.respond(self.get_text(user_id, 'error_no_data'))
                return

            if results and history_data:
                history_summary = HistorySummary(history_data, time_choice)
                signal_info = history_summary.generate_signal(selected_pair, time_choice)

                chart_plotter = TradingChartPlotter(history_data, selected_pair, 
                                                  LANGUAGES[lang]['time_options'][time_choice])
                chart_image = chart_plotter.plot_trading_chart()

                if chart_image:
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
                        temp_file_path = temp_file.name
                        temp_file.write(chart_image.read())

                    await self.client.send_file(
                        user_id,
                        temp_file_path,
                        force_document=False
                    )
                    await response.respond(signal_info)
                    os.remove(temp_file_path)
                else:
                    await response.respond(self.get_text(user_id, 'error_chart'))
                    await response.respond(
                        self.get_text(user_id, 'success',
                                    pair=selected_pair,
                                    time=LANGUAGES[lang]['time_options'][time_choice],
                                    signal=signal_info)
                    )
            else:
                await response.respond(
                    self.get_text(user_id, 'error_results', pair=asset)
                )

        except Exception as e:
            print(f"⚠️ [ERROR] Error in process_selection: {e}")
        
        await self.show_main_menu(response)

    async def show_main_menu(self, event):
        user_id = event.sender_id
        lang = self.get_user_language(user_id)
        
        await event.respond(
            self.get_text(user_id, 'welcome'),
            buttons=[
                [Button.inline(LANGUAGES[lang]['buttons']['otc'], b"otc")],
                [Button.inline(LANGUAGES[lang]['buttons']['regular'], b"regular_assets")]
            ]
        )

    async def fetch_summary_with_handling(self, asset, period, token):
        try:
            print(f"🔄 [INFO] Fetching data for {asset} with period {period}")
            results, history_data = await fetch_summary(asset, period, token)
            
            if results is None or history_data is None:
                print(f"⚠️ [ERROR] Failed to fetch data for {asset}")
                return None, None
            
            return results, history_data
        except Exception as e:
            print(f"⚠️ [ERROR] Error in fetch_summary_with_handling: {str(e)}")
            return None, None

if __name__ == "__main__":
    bot_client = TelegramBotClient()
    asyncio.run(bot_client.start_bot())

