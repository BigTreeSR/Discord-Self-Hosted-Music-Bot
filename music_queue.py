"""
Queue management for music playback
"""
from collections import deque

class GuildQueues:
    """Manages song queues for multiple guilds"""
    def __init__(self):
        self.queues = {}  # {guild_id: deque()}
        self.loop_status = {}  # {guild_id: "none" | "one" | "all"}
        self.default_platforms = {}  # {guild_id: platform}
        self.download_errors = {}  # {guild_id: count}
    
    def get_queue(self, guild_id):
        """Get the queue for a guild, creating it if it doesn't exist"""
        if guild_id not in self.queues:
            self.queues[guild_id] = deque()
        return self.queues[guild_id]
    
    def get_loop_status(self, guild_id):
        """Get the loop status for a guild"""
        return self.loop_status.get(guild_id, "none")
    
    def set_loop_status(self, guild_id, status):
        """Set the loop status for a guild"""
        self.loop_status[guild_id] = status
    
    def get_default_platform(self, guild_id):
        """Get the default platform for a guild"""
        return self.default_platforms.get(guild_id, "youtube")
    
    def set_default_platform(self, guild_id, platform):
        """Set the default platform for a guild"""
        self.default_platforms[guild_id] = platform
    
    def add_track(self, guild_id, audio_url, title):
        """Add a track to the queue"""
        self.get_queue(guild_id).append((audio_url, title))
    
    def get_current_track(self, guild_id):
        """Get the current track"""
        queue = self.get_queue(guild_id)
        if not queue:
            return None
        return queue[0]
    
    def remove_current_track(self, guild_id):
        """Remove the current track"""
        queue = self.get_queue(guild_id)
        if queue:
            return queue.popleft()
        return None
    
    def rotate_queue(self, guild_id):
        """Rotate the queue by moving the first item to the end"""
        queue = self.get_queue(guild_id)
        if queue:
            queue.rotate(-1)
    
    def clear_queue(self, guild_id):
        """Clear the queue for a guild"""
        if guild_id in self.queues:
            self.queues[guild_id].clear()
    
    def queue_length(self, guild_id):
        """Get the length of the queue"""
        return len(self.queues.get(guild_id, []))
    
    def increment_error_count(self, guild_id):
        """Increment the error count for a guild"""
        if guild_id not in self.download_errors:
            self.download_errors[guild_id] = 0
        self.download_errors[guild_id] += 1
    
    def get_error_count(self, guild_id):
        """Get the error count for a guild"""
        return self.download_errors.get(guild_id, 0)
    
    def reset_error_count(self, guild_id):
        """Reset the error count for a guild"""
        self.download_errors[guild_id] = 0

# Create a global instance
guild_queues = GuildQueues()