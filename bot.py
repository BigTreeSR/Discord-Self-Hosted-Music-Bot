"""
Bot initialization and setup
"""
import discord
from discord.ext import commands
from music_commands import register_music_commands

def setup_bot():
    """Set up and configure the Discord bot"""
    # Set up intents
    intents = discord.Intents.default()
    intents.message_content = True
    
    # Create bot instance
    bot = commands.Bot(command_prefix="!", intents=intents)
    
    # Register event handlers
    @bot.event
    async def on_ready():
        await bot.tree.sync()
        print(f"{bot.user} is online!")
    
    # Register commands
    register_music_commands(bot)
    
    return bot