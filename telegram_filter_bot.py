import json
import os
import threading
import time
import random
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext, MessageHandler, CallbackQueryHandler

# Load environment variables from .env file
load_dotenv()

# File to store filters
FILTERS_FILE = 'chat_filters.json'

# Store original message IDs to track edits
original_messages = {}

# Store self-destruct timers
self_destruct_timers = {}

# Store last good morning time per chat to prevent spam
last_good_morning = {}

# Settings functionality removed as requested

def schedule_self_destruct(context, chat_id, message_id, delay_seconds):
    """Schedule a message for self-destruction after a delay"""
    def delete_message_job():
        time.sleep(delay_seconds)
        try:
            context.bot.delete_message(chat_id=chat_id, message_id=message_id)
            print(f"Message {message_id} in chat {chat_id} was self-destructed after {delay_seconds} seconds")
        except Exception as e:
            print(f"Could not delete message {message_id}: {e}")
        finally:
            # Clean up timer reference
            if message_id in self_destruct_timers:
                del self_destruct_timers[message_id]
    
    # Cancel any existing timer for this message
    if message_id in self_destruct_timers:
        try:
            self_destruct_timers[message_id].cancel()
        except:
            pass
    
    # Create and start new timer
    timer = threading.Timer(0, delete_message_job)
    timer.start()
    self_destruct_timers[message_id] = timer


def get_good_morning_shayari():
    """Return a random good morning shayari with cute emojis"""
    shayaris = [
        "🌞 सुबह की धूप में तुम्हारा नाम लिखूंगा,\n"
        "ताकि हर किरण तुम्हें गुड मॉर्निंग कहे! 🌼\n"
        "Good Morning Everyone! 🌸✨",
        
        "🌅 मोरनिंग हुई तो सबको जगा दूंगा,\n"
        "तुम्हारी मुस्कान के लिए इंतज़ार करूंगा! 💫\n"
        "Good Morning Beautiful Souls! 🌟😊",
        
        "🌻 सूरज ने आज भी तुम्हारे लिए खिड़की खोली है,\n"
        "उठो और इस नए दिन को गले लगाओ! 🌈\n"
        "Good Morning Champions! 🏆💫",
        
        "🌼 सुबह की ठंडी हवा में तुम्हारा नाम फिसफिसाऊंगा,\n"
        "ताकि प्यार से जग जाओ सब! 💕\n"
        "Good Morning Sweethearts! 🥰🌺",
        
        "✨ नई सुबह, नए सपने, नई शुरुआत!\n"
        "आज का दिन हमारे साथ मुस्कुराए! 🌟\n"
        "Good Morning Dreamers! 🌙➡️☀️",
        
        "🌸 सुबह की पहली किरण तुम्हारे दरवाज़े पर खड़ी है,\n"
        "उठो और इस खुशियों भरे दिन का स्वागत करो! 🎉\n"
        "Good Morning Stars! ⭐✨",
        
        "💫 मोरनिंग... मोरनिंग... सबको जगा रहा हूं,\n"
        "तुम्हारी खुशियां बढ़ाने के लिए आया हूं! 🎈\n"
        "Good Morning Sunshine! ☀️🌻",
        
        "🌈 आज की सुबह खास है, इसे ख़ास बनाओ,\n"
        "तुम्हारे साथ हर पल खुशियों से भरा है! 🥂\n"
        "Good Morning Special Ones! 🎊💖"
    ]
    return random.choice(shayaris)

# Settings functionality removed - using default values

class FilterBot:
    def __init__(self):
        self.filters_data = self.load_filters()
    
    def load_filters(self):
        """Load filters from JSON file"""
        if os.path.exists(FILTERS_FILE):
            with open(FILTERS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    def save_filters(self):
        """Save filters to JSON file"""
        with open(FILTERS_FILE, 'w') as f:
            json.dump(self.filters_data, f, indent=2)
    
    def get_chat_filters(self, chat_id):
        """Get filters for a specific chat"""
        chat_id_str = str(chat_id)
        if chat_id_str not in self.filters_data:
            self.filters_data[chat_id_str] = {}
        return self.filters_data[chat_id_str]
    
    def add_filter(self, chat_id, trigger, reply, media_type=None, file_id=None):
        """Add a new filter for a chat"""
        chat_filters = self.get_chat_filters(chat_id)
        if media_type and file_id:
            # Store media information
            chat_filters[trigger.lower()] = {
                "type": "media",
                "media_type": media_type,
                "file_id": file_id,
                "caption": reply
            }
        else:
            # Store text reply
            chat_filters[trigger.lower()] = {
                "type": "text",
                "content": reply
            }
        self.save_filters()
    
    def remove_filter(self, chat_id, trigger):
        """Remove a filter from a chat"""
        chat_filters = self.get_chat_filters(chat_id)
        if trigger.lower() in chat_filters:
            del chat_filters[trigger.lower()]
            self.save_filters()
            return True
        return False
    
    def remove_all_filters(self, chat_id):
        """Remove all filters from a chat"""
        chat_id_str = str(chat_id)
        if chat_id_str in self.filters_data:
            del self.filters_data[chat_id_str]
            self.save_filters()
            return True
        return False
    
    def get_reply_for_trigger(self, chat_id, message_text):
        """Check if message contains a trigger and return reply"""
        chat_filters = self.get_chat_filters(chat_id)
        
        # Check for exact match first
        lower_text = message_text.lower()
        for trigger, reply_data in chat_filters.items():
            if trigger in lower_text:
                return reply_data
        
        return None

# Initialize the bot
bot_instance = FilterBot()

def start(update: Update, context: CallbackContext):
    """Start command handler"""
    welcome_message = (
        "Welcome to the Filter Bot!\n\n"
        "Filters are case insensitive; every time someone says your trigger words, "
        "the bot will reply something else! Can be used to create your own commands.\n\n"
        "Commands:\n"
        "- /filter &lt;trigger&gt; &lt;reply&gt;: Every time someone says \"trigger\", the bot will reply with \"sentence\". For multiple word filters, quote the trigger.\n"
        "- /filters: List all chat filters.\n"
        "- /stop &lt;trigger&gt;: Stop the bot from replying to \"trigger\".\n"
        "- /stopall: Stop ALL filters in the current chat. This cannot be undone."
    )
    
    # Create inline keyboard with two buttons
    keyboard = [
        [InlineKeyboardButton("ADD TO GROUP", url=f"https://t.me/{context.bot.username}?startgroup=true")],
        [InlineKeyboardButton("GROUP", url="https://t.me/last_promise_chatting_212")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(welcome_message, reply_markup=reply_markup)

def filter_command(update: Update, context: CallbackContext):
    """Handle /filter command to add new filters"""
    chat_id = update.effective_message.chat_id
    message = update.effective_message
    
    # Check if reply contains media
    media_type = None
    file_id = None
    
    if message.reply_to_message:
        reply_msg = message.reply_to_message
        # Check for different media types
        if reply_msg.photo:
            media_type = "photo"
            file_id = reply_msg.photo[-1].file_id  # Get highest quality
        elif reply_msg.video:
            media_type = "video"
            file_id = reply_msg.video.file_id
        elif reply_msg.document:
            media_type = "document"
            file_id = reply_msg.document.file_id
        elif reply_msg.audio:
            media_type = "audio"
            file_id = reply_msg.audio.file_id
        elif reply_msg.voice:
            media_type = "voice"
            file_id = reply_msg.voice.file_id
        elif reply_msg.sticker:
            media_type = "sticker"
            file_id = reply_msg.sticker.file_id
    
    # Extract trigger from command
    command_text = message.text
    args = command_text.split(' ', 1)
    
    if len(args) < 2:
        update.message.reply_text("Usage: /filter &lt;trigger&gt; [reply text]\nReply to a media message or provide text after trigger.")
        return
    
    # Parse trigger and optional reply text
    trigger_part = args[1]
    reply_text = ""
    
    # Handle quoted triggers
    if trigger_part.startswith('"'):
        end_quote = trigger_part.find('"', 1)
        if end_quote != -1:
            trigger = trigger_part[1:end_quote]
            reply_text = trigger_part[end_quote+1:].lstrip()
        else:
            update.message.reply_text("Invalid quoted trigger. Use: /filter \"trigger\" [reply text]")
            return
    else:
        # Split by first space to separate trigger from reply
        parts = trigger_part.split(' ', 1)
        trigger = parts[0]
        if len(parts) > 1:
            reply_text = parts[1]
    
    # Add the filter
    bot_instance.add_filter(chat_id, trigger, reply_text, media_type, file_id)
    
    update.message.reply_text(f"filter saved on this {trigger}")

def filters_command(update: Update, context: CallbackContext):
    """Handle /filters command to list all filters"""
    chat_id = update.effective_message.chat_id
    chat_filters = bot_instance.get_chat_filters(chat_id)
    
    if not chat_filters:
        update.message.reply_text("No filters in this chat.")
        return
    
    reply_text = "Filters in this chat:\n\n"
    for trigger, reply_data in chat_filters.items():
        if reply_data["type"] == "media":
            media_type = reply_data["media_type"]
            caption = reply_data.get("caption", "")
            reply_text += f'• "{trigger}" -> [{media_type.upper()} with caption: "{caption}"]\n'
        else:
            content = reply_data["content"]
            reply_text += f'• "{trigger}" -> "{content}"\n'
    
    update.message.reply_text(reply_text)

def stop_command(update: Update, context: CallbackContext):
    """Handle /stop command to remove a specific filter"""
    chat_id = update.effective_message.chat_id
    message_text = update.effective_message.text
    
    args = message_text.split(' ', 1)
    
    if len(args) < 2:
        update.message.reply_text("Usage: /stop &lt;trigger&gt;")
        return
    
    trigger = args[1].strip('"')
    
    # Handle quoted triggers
    if message_text.startswith('/stop "') and '"' in message_text[len('/stop "'):]:
        parts = message_text.split('"')
        if len(parts) >= 2:
            trigger = parts[1]
    
    if bot_instance.remove_filter(chat_id, trigger):
        update.message.reply_text(f'Removed filter: "{trigger}"')
    else:
        update.message.reply_text(f'Filter "{trigger}" not found.')

def stopall_command(update: Update, context: CallbackContext):
    """Handle /stopall command to remove all filters"""
    chat_id = update.effective_message.chat_id
    
    if bot_instance.remove_all_filters(chat_id):
        update.message.reply_text("All filters removed from this chat.")
    else:
        update.message.reply_text("No filters to remove in this chat.")

def goodmorning_command(update: Update, context: CallbackContext):
    """Handle /goodmorning command to send good morning message with member mentions (excluding command user)"""
    chat_id = update.effective_message.chat_id
    command_user_id = update.effective_user.id
    command_user_name = update.effective_user.first_name
    
    # Only allow in group chats
    if update.effective_chat.type not in ['group', 'supergroup']:
        update.message.reply_text("This command only works in group chats!")
        return
    
    try:
        # Get chat members - try multiple approaches to get more members
        member_mentions = []
        processed_user_ids = set()  # To avoid duplicates
        
        # Approach 1: Get chat administrators (always available)
        try:
            chat_admins = context.bot.get_chat_administrators(chat_id)
            for admin in chat_admins:
                user = admin.user
                # Skip bots, command user, and duplicates
                if not user.is_bot and user.id != command_user_id and user.id not in processed_user_ids:
                    member_mentions.append(f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})")
                    processed_user_ids.add(user.id)
        except Exception as admin_error:
            print(f"Could not get chat administrators: {admin_error}")
        
        # Approach 2: Try to get recent message senders (if bot has access)
        try:
            # This is a workaround - get recent messages to identify active members
            # Note: This requires the bot to have access to message history
            updates = context.bot.get_updates(limit=50)
            for update in updates:
                if update.message and update.message.chat.id == chat_id:
                    user = update.message.from_user
                    if not user.is_bot and user.id != command_user_id and user.id not in processed_user_ids:
                        member_mentions.append(f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})")
                        processed_user_ids.add(user.id)
        except Exception as history_error:
            print(f"Could not get message history: {history_error}")
        
        # Approach 3: Mention common group roles (if applicable)
        # This is a fallback for when we can't get specific members
        
        # Get the shayari
        shayari_message = get_good_morning_shayari()
        
        # Create message with mentions
        if member_mentions:
            # Limit mentions to avoid spam and Telegram limits (max ~50 mentions per message)
            limited_mentions = member_mentions[:8]  # Increased limit since we're getting more members
            mention_text = " ".join(limited_mentions)
            # Include the command user's name in the greeting
            full_message = f"Good morning {command_user_name}! 🌞\n\n{mention_text}\n\n{shayari_message}"
        else:
            # Fallback if no other members found
            full_message = f"Good morning {command_user_name}! 🌞\n\n{shayari_message}"
        
        # Send the message
        sent_message = update.message.reply_text(
            full_message, 
            parse_mode='Markdown'
        )
        print(f"Good morning message with mentions (excluding {command_user_name}) sent to chat {chat_id}")
        
    except Exception as e:
        # Fallback to simple message if mentions fail
        try:
            shayari_message = get_good_morning_shayari()
            update.message.reply_text(f"Good morning {command_user_name}! 🌞\n\n{shayari_message}")
            print(f"Good morning message sent without mentions to chat {chat_id}")
        except Exception as fallback_error:
            update.message.reply_text("Sorry, I couldn't send the good morning message right now.")
            print(f"Error sending good morning message: {e}")

def settings_command(update: Update, context: CallbackContext):
    """Handle /settings command to show bot settings"""
    global bot_settings
    
    # Get current settings
    self_destruct_time = bot_settings.get("self_destruct_time", 0)
    
    # Self-destruct status
    destruct_status = f"{self_destruct_time}s" if self_destruct_time > 0 else "Disabled"
    destruct_checkmark = "✅" if self_destruct_time > 0 else "⭕"
    
    message_text = (
        "Bot Settings\n\n"
        f"{destruct_checkmark} Self-Destruct ({destruct_status})\n"
        "Auto-delete bot messages after set time"
    )
    
    # Create inline keyboard with self-destruct setting
    keyboard = [
        [InlineKeyboardButton("Self-Destruct", callback_data="toggle_self_destruct_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    update.message.reply_text(message_text, reply_markup=reply_markup)

def handle_settings_callback(update: Update, context: CallbackContext):
    """Handle callback queries for settings buttons"""
    global bot_settings
    query = update.callback_query
    query.answer()
    
    callback_data = query.data
    user_id = query.from_user.id
    chat_id = query.message.chat_id
    message_id = query.message.message_id
    
    if callback_data == "start_settings":
        # Handle settings button from start command - show main settings
        self_destruct_time = bot_settings.get("self_destruct_time", 0)
        
        # Self-destruct status
        destruct_status = f"{self_destruct_time}s" if self_destruct_time > 0 else "Disabled"
        destruct_checkmark = "✅" if self_destruct_time > 0 else "⭕"
        
        message_text = (
            "Bot Settings\n\n"
            f"{destruct_checkmark} Self-Destruct ({destruct_status})\n"
            "Auto-delete bot messages after set time"
        )
        
        # Create inline keyboard with self-destruct setting
        keyboard = [
            [InlineKeyboardButton("Self-Destruct", callback_data="toggle_self_destruct_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text=message_text, reply_markup=reply_markup)
        
    elif callback_data == "toggle_self_destruct_menu":
        # Show self-destruct time adjustment menu
        current_time = bot_settings.get("self_destruct_time", 0)
        status = f"{current_time}s" if current_time > 0 else "Disabled"
        
        message_text = f"Self-Destruct Timer\nCurrent: {status}\n\nAdjust the time for auto-deletion:"
        
        # Create buttons for adjusting time
        keyboard = [
            [InlineKeyboardButton("-10s", callback_data="decrease_time_10"),
             InlineKeyboardButton("-1s", callback_data="decrease_time_1"),
             InlineKeyboardButton("Reset", callback_data="reset_time"),
             InlineKeyboardButton("+1s", callback_data="increase_time_1"),
             InlineKeyboardButton("+10s", callback_data="increase_time_10")],
            [InlineKeyboardButton("Back to Settings", callback_data="back_to_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text=message_text, reply_markup=reply_markup)
    
    elif callback_data.startswith("increase_time_") or callback_data.startswith("decrease_time_") or callback_data == "reset_time":
        # Handle time adjustments
        current_time = bot_settings.get("self_destruct_time", 0)
        
        if callback_data == "increase_time_1":
            current_time += 1
        elif callback_data == "increase_time_10":
            current_time += 10
        elif callback_data == "decrease_time_1":
            current_time = max(0, current_time - 1)  # Prevent negative values
        elif callback_data == "decrease_time_10":
            current_time = max(0, current_time - 10)  # Prevent negative values
        elif callback_data == "reset_time":
            current_time = 0  # Disable self-destruct
        
        # Update settings
        bot_settings["self_destruct_time"] = current_time
        save_settings(bot_settings)
        
        # Refresh the self-destruct menu
        status = f"{current_time}s" if current_time > 0 else "Disabled"
        message_text = f"Self-Destruct Timer\nCurrent: {status}\n\nAdjust the time for auto-deletion:"
        
        # Create buttons for adjusting time
        keyboard = [
            [InlineKeyboardButton("-10s", callback_data="decrease_time_10"),
             InlineKeyboardButton("-1s", callback_data="decrease_time_1"),
             InlineKeyboardButton("Reset", callback_data="reset_time"),
             InlineKeyboardButton("+1s", callback_data="increase_time_1"),
             InlineKeyboardButton("+10s", callback_data="increase_time_10")],
            [InlineKeyboardButton("Back to Settings", callback_data="back_to_settings")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text=message_text, reply_markup=reply_markup)
    
    elif callback_data == "back_to_settings":
        # Go back to main settings
        self_destruct_time = bot_settings.get("self_destruct_time", 0)
        
        # Self-destruct status
        destruct_status = f"{self_destruct_time}s" if self_destruct_time > 0 else "Disabled"
        destruct_checkmark = "✅" if self_destruct_time > 0 else "⭕"
        
        message_text = (
            "Bot Settings\n\n"
            f"{destruct_checkmark} Self-Destruct ({destruct_status})\n"
            "Auto-delete bot messages after set time"
        )
        
        # Create inline keyboard with self-destruct setting
        keyboard = [
            [InlineKeyboardButton("Self-Destruct", callback_data="toggle_self_destruct_menu")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        query.edit_message_text(text=message_text, reply_markup=reply_markup)

def should_send_good_morning(chat_id):
    """Check if we should send good morning message (once per day, morning hours)"""
    current_time = time.time()
    last_time = last_good_morning.get(chat_id, 0)
    
    # Check if 24 hours have passed
    if current_time - last_time < 24 * 3600:
        return False
    
    # Check if it's morning time (6 AM to 10 AM)
    current_hour = time.localtime().tm_hour
    if current_hour < 6 or current_hour > 10:
        return False
    
    return True


def handle_message(update: Update, context: CallbackContext):
    """Handle incoming messages and check for triggers"""
    chat_id = update.effective_message.chat_id
    message_text = update.effective_message.text
    
    # Check for auto good morning (only in group chats)
    if update.effective_chat.type in ['group', 'supergroup']:
        if should_send_good_morning(chat_id):
            try:
                # Get chat members - try multiple approaches
                member_mentions = []
                processed_user_ids = set()
                
                # Approach 1: Get chat administrators
                try:
                    chat_admins = context.bot.get_chat_administrators(chat_id)
                    for admin in chat_admins:
                        user = admin.user
                        if not user.is_bot and user.id not in processed_user_ids:
                            member_mentions.append(f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})")
                            processed_user_ids.add(user.id)
                except Exception as admin_error:
                    print(f"Could not get chat administrators: {admin_error}")
                
                # Approach 2: Try to get recent message senders
                try:
                    updates = context.bot.get_updates(limit=50)
                    for update in updates:
                        if update.message and update.message.chat.id == chat_id:
                            user = update.message.from_user
                            if not user.is_bot and user.id not in processed_user_ids:
                                member_mentions.append(f"@{user.username}" if user.username else f"[{user.first_name}](tg://user?id={user.id})")
                                processed_user_ids.add(user.id)
                except Exception as history_error:
                    print(f"Could not get message history: {history_error}")
                
                # Get the shayari
                shayari_message = get_good_morning_shayari()
                
                # Create message with mentions
                if member_mentions:
                    limited_mentions = member_mentions[:8]  # Increased limit for auto messages too
                    mention_text = " ".join(limited_mentions)
                    full_message = f"{mention_text}\n\n{shayari_message}"
                else:
                    full_message = shayari_message
                
                # Send the message
                context.bot.send_message(
                    chat_id=chat_id, 
                    text=full_message,
                    parse_mode='Markdown'
                )
                last_good_morning[chat_id] = time.time()
                print(f"Sent good morning message with mentions to chat {chat_id}")
            except Exception as e:
                # Fallback to simple message
                try:
                    shayari_message = get_good_morning_shayari()
                    context.bot.send_message(chat_id=chat_id, text=shayari_message)
                    print(f"Sent good morning message without mentions to chat {chat_id}")
                except Exception as fallback_error:
                    print(f"Could not send good morning message: {e}")
    
    if not message_text:
        return
    
    reply_data = bot_instance.get_reply_for_trigger(chat_id, message_text)
    
    if reply_data:
        if reply_data["type"] == "media":
            # Send media with caption
            media_type = reply_data["media_type"]
            file_id = reply_data["file_id"]
            caption = reply_data.get("caption", "")
            
            if media_type == "photo":
                sent_message = update.message.reply_photo(photo=file_id, caption=caption)
            elif media_type == "video":
                sent_message = update.message.reply_video(video=file_id, caption=caption)
            elif media_type == "document":
                sent_message = update.message.reply_document(document=file_id, caption=caption)
            elif media_type == "audio":
                sent_message = update.message.reply_audio(audio=file_id, caption=caption)
            elif media_type == "voice":
                sent_message = update.message.reply_voice(voice=file_id, caption=caption)
            elif media_type == "sticker":
                sent_message = update.message.reply_sticker(sticker=file_id)
        else:
            # Send text reply
            sent_message = update.message.reply_text(reply_data["content"])
        
        # Store the original message ID for edit tracking
        if 'sent_message' in locals() and sent_message:
            original_messages[sent_message.message_id] = {
                "chat_id": chat_id,
                "user_id": update.effective_user.id
            }
            
            # Schedule self-destruct with default time (disabled)
            self_destruct_time = 0  # Self-destruct disabled by default
            if self_destruct_time > 0:
                schedule_self_destruct(context, chat_id, sent_message.message_id, self_destruct_time)

# Edit checker feature removed as requested

def main():
    """Main function to run the bot"""
    # Get token from environment variable
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    
    if not token:
        print("Error: TELEGRAM_BOT_TOKEN environment variable not set!")
        return
    
    updater = Updater(token, use_context=True)
    dp = updater.dispatcher
    
    # Register command handlers
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("filter", filter_command))
    dp.add_handler(CommandHandler("filters", filters_command))
    dp.add_handler(CommandHandler("stop", stop_command))
    dp.add_handler(CommandHandler("stopall", stopall_command))
    dp.add_handler(CommandHandler("goodmorning", goodmorning_command))
    
    # No callback handlers needed
    
    # Register message handlers
    dp.add_handler(MessageHandler(Filters.text & ~Filters.command, handle_message))
    
    # Start the bot
    print("Bot is starting...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()