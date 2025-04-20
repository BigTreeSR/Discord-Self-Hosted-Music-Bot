"""
Discord Music Bot - Main Entry Point
"""
import os
from dotenv import load_dotenv
from bot import setup_bot

# Load environment variables
load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

if __name__ == "__main__":
    # Set up and run the bot
    bot = setup_bot()
    bot.run(TOKEN)
