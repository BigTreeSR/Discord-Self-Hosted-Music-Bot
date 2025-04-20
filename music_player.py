"""
Music player functionality
"""
import asyncio
import discord
from config import FFMPEG_OPTIONS
from music_queue import guild_queues

async def play_next_song(voice_client, guild_id, channel):
    """Play the next song in the queue"""
    if not voice_client or not voice_client.is_connected():
        return
        
    if guild_queues.queue_length(guild_id) == 0:
        await voice_client.disconnect()
        return

    audio_url, title = guild_queues.get_current_track(guild_id)

    try:
        source = discord.FFmpegOpusAudio(audio_url, **FFMPEG_OPTIONS)
        
        def after_play(error):
            loop_mode = guild_queues.get_loop_status(guild_id)
            
            if error:
                asyncio.run_coroutine_threadsafe(
                    channel.send(f"⚠️ Error playing **{title}**: {str(error)}. Skipping to next song."), 
                    voice_client.loop
                )
                # Don't loop on error
                guild_queues.remove_current_track(guild_id)
            else:
                if loop_mode == "one":
                    pass  # Don't modify the queue
                elif loop_mode == "all":
                    guild_queues.rotate_queue(guild_id)
                else:
                    guild_queues.remove_current_track(guild_id)

            asyncio.run_coroutine_threadsafe(
                play_next_song(voice_client, guild_id, channel), 
                voice_client.loop
            )

        voice_client.play(source, after=after_play)
        await channel.send(f"Now playing: **{title}**")
        
    except Exception as e:
        await channel.send(f"❌ Error playing **{title}**: {str(e)}. Skipping to next song.")
        guild_queues.remove_current_track(guild_id)
        await play_next_song(voice_client, guild_id, channel)
