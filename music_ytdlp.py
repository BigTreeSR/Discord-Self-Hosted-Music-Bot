"""
YouTube-DL wrapper for music extraction
"""
import asyncio
import yt_dlp
from music_queue import guild_queues

class MyLogger:
    """Custom YoutubeDL logger to capture errors"""
    def debug(self, msg):
        pass

    def warning(self, msg):
        pass

    def error(self, msg):
        print(f"YT-DLP Error: {msg}")

async def search_ytdlp_async(query, ydl_opts, guild_id):
    """Run YT-DLP extraction asynchronously"""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts, guild_id))

def _extract(query, ydl_opts, guild_id):
    """Extract information from YT-DLP"""
    # Reset error counter for this guild
    guild_queues.reset_error_count(guild_id)
    
    # Add custom logger to options
    ydl_opts["logger"] = MyLogger()
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(query, download=False)
            
            # Check for extraction errors in playlists
            if info and "entries" in info:
                # Count and filter out None entries (which represent failed extractions)
                original_count = len(info["entries"])
                info["entries"] = [entry for entry in info["entries"] if entry is not None]
                failed_count = original_count - len(info["entries"])
                
                if failed_count > 0:
                    guild_queues.increment_error_count(guild_id)
            
            return info
    except Exception as e:
        print(f"Extraction error: {str(e)}")
        guild_queues.increment_error_count(guild_id)
        return None

def get_audio_url_from_track(track):
    """Extract the audio URL from a track"""
    if track is None:
        return None
        
    audio_url = track.get("url")
    if not audio_url and "formats" in track:
        # Try to get audio URL from formats
        for format in track["formats"]:
            if format.get("acodec") != "none":
                audio_url = format.get("url")
                break
    
    return audio_url
