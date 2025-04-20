"""
Configuration settings for the music bot
"""

# Playlist configuration
MAX_PLAYLIST_SIZE = 100

# Platform settings
PLATFORMS = ["youtube", "soundcloud"]

# FFmpeg settings
FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn -c:a libopus -b:a 96k",
}

# YT-DLP Options
YDL_BASE_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": False,
    "ignoreerrors": True,
    "skip_download": True,
}