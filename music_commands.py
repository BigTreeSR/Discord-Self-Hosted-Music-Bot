"""
Music-related commands for the bot
"""
import discord
from discord import app_commands
from config import MAX_PLAYLIST_SIZE, YDL_BASE_OPTIONS
from utils import is_url, is_playlist_url, find_best_match, get_search_prefix
from music_queue import guild_queues
from music_ytdlp import search_ytdlp_async, get_audio_url_from_track
from music_player import play_next_song

def register_music_commands(bot):
    """Register all music-related commands with the bot"""
    
    @bot.tree.command(name="play", description="Play a song or add it to the queue.")
    @app_commands.describe(
        platform="Select the platform to search on",
        query="Song name, artist, or URL"
    )
    @app_commands.choices(platform=[
        app_commands.Choice(name="YouTube", value="youtube"),
        app_commands.Choice(name="SoundCloud", value="soundcloud"),
    ])
    async def play(interaction: discord.Interaction, platform: str, query: str):
        await interaction.response.defer()

        if interaction.user.voice is None:
            await interaction.followup.send("You must be in a voice channel.")
            return
            
        voice_channel = interaction.user.voice.channel
        if voice_channel is None:
            await interaction.followup.send("You must be in a voice channel.")
            return

        voice_client = interaction.guild.voice_client
        if voice_client is None:
            voice_client = await voice_channel.connect()
        elif voice_channel != voice_client.channel:
            await voice_client.move_to(voice_channel)

        guild_id = str(interaction.guild_id)
        guild_queues.reset_error_count(guild_id)
        guild_queues.set_default_platform(guild_id, platform)
        
        # Check if the queue limit would be exceeded
        remaining_slots = MAX_PLAYLIST_SIZE - guild_queues.queue_length(guild_id)
        if remaining_slots <= 0:
            await interaction.followup.send(f"⚠️ Queue limit of {MAX_PLAYLIST_SIZE} songs has been reached. Please remove some songs first.")
            return

        tracks_added = 0
        
        # Handle URL vs search query differently
        if is_url(query):
            # Process URL (playlist or single track)
            await _process_url(interaction, query, guild_id, remaining_slots)
        else:
            # Search for track
            await _search_and_add_track(interaction, platform, query, guild_id)
            
        # Start playback if not already playing
        if not voice_client.is_playing() and not voice_client.is_paused():
            await play_next_song(voice_client, guild_id, interaction.channel)
            
    async def _process_url(interaction, query, guild_id, remaining_slots):
        """Process a URL (playlist or single track)"""
        # Check if this is likely a playlist URL
        if is_playlist_url(query):
            # Only fetch limited number of items (remaining queue slots, max 100)
            ydl_options = YDL_BASE_OPTIONS.copy()
            ydl_options["playlist_items"] = f"1-{remaining_slots}"
            await interaction.followup.send(f"🎵 Detected playlist URL - limiting to first {remaining_slots} songs to fit queue limit.")
        else:
            ydl_options = YDL_BASE_OPTIONS.copy()
            
        await interaction.followup.send(f"🔍 Processing URL: `{query}`")
        
        try:
            result = await search_ytdlp_async(query, ydl_options, guild_id)
            
            # If extraction completely failed
            if result is None:
                await interaction.followup.send("❌ Failed to extract any information from this URL.")
                return 0
                
            is_playlist = False
            if "entries" in result:
                tracks = result["entries"]
                # Check if this is a playlist
                if len(tracks) > 1:
                    is_playlist = True
                    playlist_title = result.get("title", "Unknown Playlist")
                    original_size = result.get("playlist_count", len(tracks))
                    
                    # Inform user about the playlist
                    if original_size > MAX_PLAYLIST_SIZE:
                        await interaction.followup.send(f"📋 Found playlist: **{playlist_title}** ({original_size} tracks, limited to first {MAX_PLAYLIST_SIZE})")
                    else:
                        await interaction.followup.send(f"📋 Found playlist: **{playlist_title}** ({len(tracks)} tracks)")
            else:
                tracks = [result]

            # Process the tracks
            tracks_added = 0
            unavailable_count = 0
            
            for track in tracks:
                if track is None:
                    unavailable_count += 1
                    continue
                    
                # Get audio URL
                audio_url = get_audio_url_from_track(track)
                if not audio_url:
                    unavailable_count += 1
                    continue
                    
                title = track.get("title", "Untitled")
                
                # Check if we've hit the queue limit
                if guild_queues.queue_length(guild_id) >= MAX_PLAYLIST_SIZE:
                    await interaction.followup.send(f"⚠️ Queue limit of {MAX_PLAYLIST_SIZE} songs reached. Added {tracks_added} songs.")
                    break
                
                guild_queues.add_track(guild_id, audio_url, title)
                tracks_added += 1
            
            # Report unavailable videos
            error_count = guild_queues.get_error_count(guild_id)
            if unavailable_count > 0 or error_count > 0:
                total_errors = unavailable_count + error_count
                if is_playlist:
                    await interaction.followup.send(f"⚠️ {total_errors} video(s) in the playlist were unavailable or restricted and were skipped.")
                else:
                    await interaction.followup.send(f"⚠️ {total_errors} video(s) were unavailable or restricted and were skipped.")
            
            # Final status message
            if tracks_added > 0:
                await interaction.followup.send(f"➕ Added {tracks_added} track(s) to queue!")
            else:
                await interaction.followup.send("❌ No playable tracks found! The videos might be unavailable, age-restricted, or region-locked.")
                
            return tracks_added
                
        except Exception as e:
            await interaction.followup.send(f"❌ Error processing request: {str(e)}")
            return 0
            
    async def _search_and_add_track(interaction, platform, query, guild_id):
        """Search for a track and add it to the queue"""
        search_prefix = get_search_prefix(platform)
        search_query = f"{search_prefix}{query}"
        
        await interaction.followup.send(f"🔍 Searching on **{platform}** for: `{query}`")
        
        # Phase 1: Get basic metadata with extract_flat
        flat_options = YDL_BASE_OPTIONS.copy()
        flat_options["extract_flat"] = True
        
        try:
            # Get basic metadata first
            basic_results = await search_ytdlp_async(search_query, flat_options, guild_id)
            
            if basic_results is None or "entries" not in basic_results or not basic_results["entries"]:
                await interaction.followup.send("❌ No results found!")
                return 0
                
            # Find best match based on titles
            valid_entries = [entry for entry in basic_results["entries"] if entry is not None]
            if not valid_entries:
                await interaction.followup.send("❌ No valid results found!")
                return 0
                
            best_match = find_best_match(valid_entries, query)
            
            # Phase 2: Download complete info only for the best match
            full_options = YDL_BASE_OPTIONS.copy()
            
            # Get video/audio URL
            best_url = best_match.get("url", "")
            if not best_url and "id" in best_match:
                # Construct URL based on platform and ID
                if platform == "youtube":
                    best_url = f"https://www.youtube.com/watch?v={best_match['id']}"
                elif platform == "soundcloud" and "webpage_url" in best_match:
                    best_url = best_match["webpage_url"]
                else:
                    best_url = best_match.get("webpage_url", best_match.get("id", ""))
            
            if not best_url:
                await interaction.followup.send("❌ Could not determine URL for the best match.")
                return 0
                
            await interaction.followup.send(f"✅ Found best match: **{best_match.get('title', 'Unknown')}**")
            
            # Get full details for best match
            full_result = await search_ytdlp_async(best_url, full_options, guild_id)
            
            if full_result is None:
                await interaction.followup.send("❌ Failed to extract complete information for the selected track.")
                return 0
                
            # Get audio URL
            audio_url = get_audio_url_from_track(full_result)
            if not audio_url:
                await interaction.followup.send("❌ Could not extract audio URL from the selected track.")
                return 0
                
            title = full_result.get("title", "Untitled")
            guild_queues.add_track(guild_id, audio_url, title)
            
            await interaction.followup.send(f"➕ Added **{title}** to the queue!")
            return 1
            
        except Exception as e:
            await interaction.followup.send(f"❌ Error during search: {str(e)}")
            return 0

    # Queue control commands
    @bot.tree.command(name="loop", description="Loop the current song.")
    async def loop(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        guild_queues.set_loop_status(guild_id, "one")
        await interaction.response.send_message("🔂 Looping current song!")

    @bot.tree.command(name="loopqueue", description="Loop the entire playlist queue.")
    async def loopqueue(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        guild_queues.set_loop_status(guild_id, "all")
        await interaction.response.send_message("🔁 Looping entire queue!")

    @bot.tree.command(name="unloop", description="Stop looping.")
    async def unloop(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        guild_queues.set_loop_status(guild_id, "none")
        await interaction.response.send_message("⏹️ Looping disabled.")

    # Playback control commands
    @bot.tree.command(name="leave", description="Disconnect the bot from voice channel and clear the queue.")
    async def leave(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        guild_id = str(interaction.guild_id)
        
        if voice_client is None:
            await interaction.response.send_message("Bot is not connected to any voice channel!")
            return
            
        # Clear the queue for this guild
        guild_queues.clear_queue(guild_id)
            
        # Stop any current playback
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            
        # Disconnect from the voice channel
        await voice_client.disconnect()
        await interaction.response.send_message("👋 Left the voice channel and cleared the queue!")

    @bot.tree.command(name="skip", description="Skip the current song.")
    async def skip(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        guild_id = str(interaction.guild_id)

        if voice_client is None or not voice_client.is_playing():
            await interaction.response.send_message("Nothing is playing to skip!")
            return

        voice_client.stop()
        await interaction.response.send_message("⏭️ Skipped current song!")

    @bot.tree.command(name="stop", description="Stop playback and clear the queue.")
    async def stop(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client
        guild_id = str(interaction.guild_id)

        if voice_client is None:
            await interaction.response.send_message("Bot is not in a voice channel!")
            return

        guild_queues.clear_queue(guild_id)
        
        if voice_client.is_playing() or voice_client.is_paused():
            voice_client.stop()
            await interaction.response.send_message("⏹️ Playback stopped and queue cleared!")
        else:
            await interaction.response.send_message("Nothing is playing!")

    @bot.tree.command(name="pause", description="Pause the current song.")
    async def pause(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client is None or not voice_client.is_playing():
            await interaction.response.send_message("Nothing is playing to pause!")
            return

        voice_client.pause()
        await interaction.response.send_message("⏸️ Playback paused!")

    @bot.tree.command(name="unpause", description="Resume playback.")
    async def unpause(interaction: discord.Interaction):
        voice_client = interaction.guild.voice_client

        if voice_client is None or not voice_client.is_paused():
            await interaction.response.send_message("Nothing is paused to resume!")
            return

        voice_client.resume()
        await interaction.response.send_message("▶️ Playback resumed!")

    @bot.tree.command(name="queue", description="Show the current song queue")
    async def queue(interaction: discord.Interaction):
        guild_id = str(interaction.guild_id)
        
        if guild_queues.queue_length(guild_id) == 0:
            await interaction.response.send_message("Queue is empty!")
            return
            
        queue_list = []
        queue = guild_queues.get_queue(guild_id)
        
        for i, (_, title) in enumerate(queue):
            prefix = "🎵 Now Playing: " if i == 0 else f"{i}. "
            queue_list.append(f"{prefix}{title}")
        
        # Create embed with pagination if needed
        embed = discord.Embed(title="Current Queue", description="\n".join(queue_list[:15]), color=0x3498db)
        
        if len(queue_list) > 15:
            embed.set_footer(text=f"And {len(queue_list) - 15} more songs...")
        
        loop_status = guild_queues.get_loop_status(guild_id)
        if loop_status == "one":
            embed.add_field(name="Loop Status", value="🔂 Looping current song", inline=False)
        elif loop_status == "all":
            embed.add_field(name="Loop Status", value="🔁 Looping entire queue", inline=False)
        
        # Add queue limit info
        embed.add_field(name="Queue Limit", value=f"{guild_queues.queue_length(guild_id)}/{MAX_PLAYLIST_SIZE} songs", inline=True)
        
        await interaction.response.send_message(embed=embed)