# Discord Music Bot

A powerful Discord music bot built with discord.py that allows you to play music from YouTube and SoundCloud in your Discord server.

## Features

- Play music from YouTube and SoundCloud
- Search for songs by name or URL
- Queue management with up to 100 songs
- Loop single songs or entire queue
- Advanced playlist handling
- Two-phase search for better song matching
- Error handling and reporting

## Requirements

- Python 3.8 or higher
- FFmpeg installed on your system
- Discord Bot Token

## Installation

1. Clone this repository:
```sh
git clone https://github.com/yourusername/discord-musicbot.git
cd discord-musicbot
```

2. Install the required dependencies:
```sh
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your Discord bot token:
```
DISCORD_TOKEN=your_discord_bot_token_here
```

4. Run the bot:
```sh
python main.py
```

## Commands

The bot uses slash commands for all interactions:

- `/play <platform> <query>` - Play a song or add it to the queue (platform can be YouTube or SoundCloud)
- `/queue` - Show the current song queue
- `/skip` - Skip the current song
- `/pause` - Pause the current song
- `/unpause` - Resume playback
- `/stop` - Stop playback and clear the queue
- `/loop` - Loop the current song
- `/loopqueue` - Loop the entire playlist queue
- `/unloop` - Stop looping
- `/leave` - Disconnect the bot from voice channel and clear the queue

## Project Structure

```
discord-musicbot/
├── main.py              # Entry point
├── bot.py               # Bot initialization
├── config.py            # Configuration settings
├── utils.py             # Utility functions
├── music/
│   ├── __init__.py      # Package marker
│   ├── player.py        # Music player
│   ├── queue.py         # Queue management
│   └── ytdlp.py         # YouTube-DL handling
├── commands/
│   ├──