# Telegram Filter Bot

A Telegram bot that allows users to create custom filters. When someone says a trigger word or phrase, the bot will automatically reply with a predefined message.

## Features

- Case-insensitive filters
- Support for multi-word triggers using quotes
- Per-chat filter storage
- Commands to manage filters

## Commands

- `/filter <trigger> <reply>`: Every time someone says "trigger", the bot will reply with "sentence". For multiple word filters, quote the trigger.
- `/filters`: List all chat filters.
- `/stop <trigger>`: Stop the bot from replying to "trigger".
- `/stopall`: Stop ALL filters in the current chat. This cannot be undone.

## Setup

1. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Get a bot token from [@BotFather](https://t.me/BotFather) on Telegram.

3. Set the environment variable:
   ```
   export TELEGRAM_BOT_TOKEN="your_bot_token_here"
   ```

4. Run the bot:
   ```
   python telegram_filter_bot.py
   ```

## How to Use

1. Add the bot to a group or start a chat with it.
2. Use `/filter hello Hello there!` to make the bot respond with "Hello there!" every time someone says "hello".
3. Use `/filter "good morning" Good morning, everyone!` to create a filter for the phrase "good morning".
4. Use `/filters` to see all active filters in the current chat.
5. Use `/stop hello` to remove the "hello" filter.
6. Use `/stopall` to remove all filters in the current chat.

## Storage

Filters are stored in `chat_filters.json`, organized by chat ID. The bot persists filters between restarts.

## Note

- Filters are case-insensitive.
- The bot only responds to exact phrase matches within messages.
- Be careful with `/stopall` as it cannot be undone.# last_promise
