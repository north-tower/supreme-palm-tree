from telethon import TelegramClient, events, Button, types
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
from language_manager import LanguageManager
from user_manager import UserManager
import json
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bot.log')
    ]
)
logger = logging.getLogger(__name__)

# Initialize managers
lang_manager = LanguageManager()
user_manager = UserManager()

class TelegramBotClient:
    def __init__(self):
        logger.info("🔄 Initializing Telegram Bot Client")
        print("🔄 [INFO] Loading environment variables from .env file.")
        load_dotenv()
        self.currency_pairs = CurrencyPairs()
        self.user_messages = {}
        self.user_request_count = {}

        self.api_id = "26422824"
        self.api_hash = "3c8f82c213fbd41b275b8b921d8ed946"
        self.bot_token = "8129679884:AAGEbC-P6_YFQFzERMiV2UevFx6uXAqSUhs"
        
        # Initialize with default admin
        self.default_admin_id = "1885741502"  # Replace with your Telegram ID
        logger.info(f"Setting up default admin with ID: {self.default_admin_id}")
        user_manager.add_admin(self.default_admin_id)

        if not all([self.api_id, self.api_hash, self.bot_token]):
            error_msg = "Missing environment variables: API_ID, API_HASH, or BOT_TOKEN"
            logger.error(error_msg)
            raise ValueError(error_msg)

        self.client = None
        logger.info("✅ Bot client initialized successfully")

    async def connect(self):
        try:
            logger.info("🚀 Attempting to connect to Telegram")
            print("🚀 [INFO] Initializing Telegram Client for the bot.")
            self.client = TelegramClient('bot', self.api_id, self.api_hash)
            
            # Test connection to Telegram API
            logger.info("Testing connection to Telegram API...")
            try:
                await self.client.connect()
                if await self.client.is_user_authorized():
                    logger.info("✅ Successfully connected to Telegram API")
                else:
                    logger.info("Starting bot with token...")
            await self.client.start(bot_token=self.bot_token)
            except Exception as e:
                logger.error(f"Failed to connect to Telegram API: {e}")
                raise

            logger.info("✅ Successfully connected to Telegram.")
            print("✅ [INFO] Successfully connected to Telegram.")
        except Exception as e:
            error_msg = f"⚠️ [ERROR] Failed to connect: {e}"
            logger.error(error_msg)
            print(error_msg)
            raise

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
                    print(f"⚠️ [ERROR] Failed to delete message: {e}")
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
            logger.info("Starting bot...")
            await self.connect()

            # Add command handlers
            logger.info("Registering command handlers...")
            self.client.add_event_handler(self.handle_start_command, events.NewMessage(pattern='/start'))
            self.client.add_event_handler(self.handle_help_command, events.NewMessage(pattern='/help'))
            self.client.add_event_handler(
                self.handle_admin_command, 
                events.NewMessage(pattern='/approve|/pending|/stats|/addadmin|/removeadmin|/listadmins')
            )
            self.client.add_event_handler(self.handle_asset_selection, events.CallbackQuery)
            logger.info("✅ Command handlers registered successfully")

            logger.info("Bot is ready to receive messages")
            await self.client.run_until_disconnected()

        except Exception as e:
            error_msg = f"⚠️ [ERROR] Failed to start bot: {e}"
            logger.error(error_msg)
            print(error_msg)
            raise

    async def handle_start_command(self, event):
        user_id = event.sender_id
        username = event.sender.username

        # Add user if new
        if user_manager.add_user(user_id, username):
            user = user_manager.get_user(user_id)
            if user['is_approved']:
                welcome_msg = lang_manager.get_text("welcome_approved")
            else:
                welcome_msg = lang_manager.get_text("welcome_pending")
        else:
            user = user_manager.get_user(user_id)
            if user['is_approved']:
                welcome_msg = lang_manager.get_text("welcome_approved")
            else:
                welcome_msg = lang_manager.get_text("welcome_trial")

        await self.show_main_menu(event, welcome_msg)

    async def show_main_menu(self, event, welcome_msg=None):
        if welcome_msg is None:
            welcome_msg = lang_manager.get_text("welcome")

        user_id = event.sender_id
        user = user_manager.get_user(user_id)
        
        if user:
            if not user['is_approved']:
                signals_msg = lang_manager.get_text("trial_signals_remaining").format(count=user['signals_remaining'])
            else:
                signals_msg = ""
        else:
            signals_msg = ""

        message = await event.respond(
            f"{welcome_msg}\n\n{signals_msg}\n\n" +
            "⚠️ *" + lang_manager.get_text("important") + "*\n\n" +
            "💡 " + lang_manager.get_text("lets_start"),
            buttons=[
                [Button.inline("1️⃣ " + lang_manager.get_text("otc_assets"), b"otc")],
                [Button.inline("2️⃣ " + lang_manager.get_text("regular_assets"), b"regular_assets")],
                [Button.inline("🌐 " + lang_manager.get_text("change_language"), b"change_language")]
            ]
        )
        await self.store_message(event.sender_id, message)

    async def handle_asset_selection(self, event):
        user_id = event.sender_id
        
        # Check if user can use signals
        if not user_manager.can_use_signal(user_id):
            user = user_manager.get_user(user_id)
            if not user:
                await event.respond(lang_manager.get_text("user_not_found"))
                return
            elif not user['is_approved']:
                # Only show pending approval message if they have no signals left
                if user['signals_remaining'] <= 0:
                    await event.respond(lang_manager.get_text("user_not_approved"))
                return
            else:
                await event.respond(lang_manager.get_text("no_signals_remaining"))
                return

        selected_asset = event.data.decode('utf-8')

        # Initialize request count for new users
        if user_id not in self.user_request_count:
            self.user_request_count[user_id] = 0

        # Increment request count
        self.user_request_count[user_id] += 1

        try:
            if selected_asset == "change_language":
                await self.show_language_selection(event)
            elif selected_asset in ["otc", "regular_assets"]:
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
            print(f"⚠️ [ERROR] Error in handle_asset_selection: {e}")
            try:
                await self.show_main_menu(event)
            except Exception as menu_error:
                print(f"⚠️ [ERROR] Failed to show main menu: {menu_error}")

    async def process_selection(self, response, selected_pair, time_choice):
        user_id = response.sender_id
        
        # Use one signal
        if not user_manager.use_signal(user_id):
            await response.respond(lang_manager.get_text("no_signals_remaining"))
            return

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
            print(f"⚠️ [ERROR] Error in process_selection: {e}")
            error_msg = await response.respond(lang_manager.get_text("error_unknown"))
            await self.store_message(response.sender_id, error_msg)
            
        # Show the main menu after processing
        await self.show_main_menu(response)
   
    async def show_language_selection(self, event):
        available_languages = {
            "en": "🇬🇧 English",
            "ru": "🇷🇺 Русский",
            "es": "🇪🇸 Español",
            "ar": "🇸🇦 العربية"
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
            print(f"🔄 [INFO] Fetching data for {asset} with period {period}")
            results, history_data = await fetch_summary(asset, period, token)

            if results is None or history_data is None:
                print(f"⚠️ [WARNING] Failed to fetch data for {asset}")
                return None, None

            return results, history_data
        except Exception as e:
            print(f"⚠️ [ERROR] Error in fetch_summary_with_handling: {str(e)}")
            return None, None

    async def handle_admin_command(self, event):
        """Handle admin commands"""
        user_id = event.sender_id
        print(f"🔍 [DEBUG] Processing admin command from user {user_id}")
        
        if not user_manager.is_admin(user_id):
            print(f"⚠️ [DEBUG] User {user_id} is not an admin")
            await event.respond(lang_manager.get_text("admin_only"))
            return

        command = event.text.split()[0][1:]  # Remove the / from the command
        args = event.text.split()[1:]
        print(f"🔍 [DEBUG] Processing command: {command} with args: {args}")

        if command == "approve":
            if not args:
                await event.respond("Usage: /approve <user_id>")
                return
            try:
                target_id = int(args[0])
                success, message = user_manager.approve_user(target_id, user_id)
                await event.respond(message)
            except ValueError:
                await event.respond("Invalid user ID")

        elif command == "activate":
            if not args:
                await event.respond("Usage: /activate <user_id>")
                return
            try:
                target_id = int(args[0])
                success, message = user_manager.activate_user(target_id, user_id)
                await event.respond(message)
            except ValueError:
                await event.respond("Invalid user ID")

        elif command == "deactivate":
            if not args:
                await event.respond("Usage: /deactivate <user_id>")
                return
            try:
                target_id = int(args[0])
                success, message = user_manager.deactivate_user(target_id, user_id)
                await event.respond(message)
            except ValueError:
                await event.respond("Invalid user ID")

        elif command == "addadmin":
            if not args:
                await event.respond("Usage: /addadmin <user_id>")
                return
            try:
                target_id = int(args[0])
                print(f"🔍 [DEBUG] Adding admin: {target_id}")
                if user_manager.add_admin(target_id):
                    await event.respond(lang_manager.get_text("admin_added"))
                else:
                    await event.respond(lang_manager.get_text("admin_already_exists"))
            except ValueError:
                await event.respond("Invalid user ID")

        elif command == "removeadmin":
            if not args:
                await event.respond("Usage: /removeadmin <user_id>")
                return
            try:
                target_id = int(args[0])
                print(f"🔍 [DEBUG] Removing admin: {target_id}")
                if str(target_id) == str(self.default_admin_id):
                    await event.respond(lang_manager.get_text("cannot_remove_default_admin"))
                    return
                if user_manager.remove_admin(target_id):
                    await event.respond(lang_manager.get_text("admin_removed"))
                else:
                    await event.respond(lang_manager.get_text("admin_not_found"))
            except ValueError:
                await event.respond("Invalid user ID")

        elif command == "listadmins":
            print("🔍 [DEBUG] Listing admins")
            admins = user_manager.get_admins()
            if not admins:
                await event.respond(lang_manager.get_text("no_admins"))
                return
            
            admin_list = []
            for admin_id in admins:
                user = user_manager.get_user(admin_id)
                username = user.get('username', 'Unknown') if user else 'Unknown'
                admin_list.append(f"ID: {admin_id}\nUsername: {username}\n")
            
            await event.respond(lang_manager.get_text("admin_list").format(admins="\n".join(admin_list)))

        elif command == "pending":
            pending_users = user_manager.get_pending_users()
            if not pending_users:
                await event.respond(lang_manager.get_text("no_pending_users"))
                return

            users_list = []
            for user_id, user in pending_users.items():
                users_list.append(f"ID: {user_id}\nUsername: {user.get('username', 'Unknown')}\nJoined: {user['joined_date']}\n")

            await event.respond(lang_manager.get_text("pending_users").format(users="\n".join(users_list)))

        elif command == "stats":
            if not args:
                await event.respond("Usage: /stats <user_id>")
                return
            try:
                target_id = int(args[0])
                stats = user_manager.get_user_stats(target_id)
                if stats:
                    status = "Approved" if stats['is_approved'] else "Pending"
                    active_status = "Active" if stats['is_active'] else "Deactivated"
                    admin_status = "Admin" if stats['is_admin'] else "User"
                    signals = "Unlimited" if stats['signals_remaining'] == float('inf') else stats['signals_remaining']
                    await event.respond(lang_manager.get_text("user_stats").format(
                        username=stats['username'],
                        status=f"{status} ({active_status}) - {admin_status}",
                        signals=signals,
                        joined=stats['joined_date']
                    ))
                else:
                    await event.respond("User not found")
            except ValueError:
                await event.respond("Invalid user ID")

    async def handle_help_command(self, event):
        """Handle the help command"""
        user_id = event.sender_id
        is_admin = user_manager.is_admin(user_id)
        
        # Build help message
        help_message = [
            lang_manager.get_text("help_title"),
            "\n",
            lang_manager.get_text("help_general"),
            "\n",
            lang_manager.get_text("help_trading")
        ]
        
        # Add admin commands if user is admin
        if is_admin:
            help_message.extend([
                "\n",
                lang_manager.get_text("help_admin")
            ])
        
        # Add footer
        help_message.extend([
            "\n",
            lang_manager.get_text("help_footer")
        ])
        
        # Send the help message
        await event.respond("".join(help_message))

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
            print(f"⚠️ [ERROR] Error in prompting for time: {e}")

    # Helper method: Handle time input
    async def _handle_time_input(self, response, selected_pair):
        try:
            time_choice = int(response.data.decode('utf-8'))
            print(f"✅ [INFO] Time selected: {time_choice} minutes for pair {selected_pair}")

            # Process the selection
            await self.process_selection(response, selected_pair, time_choice)

        except ValueError as ve:
            print(f"⚠️ [ERROR] Invalid time input: {ve}")
        except Exception as e:
            print(f"⚠️ [ERROR] Error in process_time_input: {e}")

    async def display_currency_pairs(self, event, asset_type):
        try:
            pairs = await self.currency_pairs.fetch_pairs(asset_type)
            buttons = self.generate_buttons(pairs, asset_type)

            # Try to edit the message first
            try:
                message = await event.edit(
                    lang_manager.get_text("select_currency_pair"),
                    buttons=buttons
                )
            except Exception as edit_error:
                # If edit fails, send a new message
                print(f"⚠️ [INFO] Failed to edit message, sending new one: {edit_error}")
                message = await event.respond(
                    lang_manager.get_text("select_currency_pair"),
                    buttons=buttons
                )
            
            await self.store_message(event.sender_id, message)
        except Exception as e:
            print(f"⚠️ [ERROR] Error in display_currency_pairs: {e}")
            # Try to show main menu as fallback
            await self.show_main_menu(event)

if __name__ == "__main__":
    try:
        logger.info("Starting bot application...")
        bot_client = TelegramBotClient()
        asyncio.run(bot_client.start_bot())
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)

