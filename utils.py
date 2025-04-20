"""
Utility functions for the music bot
"""
import re
import difflib

def get_platform_from_url(url):
    """Determine the platform from a URL"""
    if "youtube.com" in url or "youtu.be" in url:
        return "youtube"
    elif "soundcloud.com" in url:
        return "soundcloud"
    return None

def is_url(text):
    """Check if the text is a URL"""
    return bool(re.match(r'https?://', text))

def is_playlist_url(url):
    """Check if the URL is a playlist"""
    return "playlist" in url or "list=" in url

def find_best_match(tracks, original_query):
    """Find best matching track from search results based on user's query"""
    # Clean the original query for better matching
    clean_query = original_query.lower().strip()
    
    # Extract just the search term from search prefix if present
    if ":" in clean_query:
        parts = clean_query.split(":", 1)
        if len(parts) > 1 and parts[0].endswith("search"):
            clean_query = parts[1].strip()
    
    # If there's only one result, return it
    if len(tracks) == 1:
        return tracks[0]
    
    # Compare each track title with the query
    best_match = None
    highest_ratio = 0
    
    for track in tracks:
        if track is None or "title" not in track:
            continue
            
        title = track["title"].lower()
        ratio = difflib.SequenceMatcher(None, clean_query, title).ratio()
        
        # Boost ratio if exact words from query appear in title
        query_words = clean_query.split()
        for word in query_words:
            if word in title and len(word) > 2:  # Only count meaningful words
                ratio += 0.1
                
        if ratio > highest_ratio:
            highest_ratio = ratio
            best_match = track
    
    # Return the best match or the first track if no good match
    return best_match if best_match else tracks[0]

def get_search_prefix(platform):
    """Get the search prefix for a platform"""
    if platform == "youtube":
        return "ytsearch10:"
    elif platform == "soundcloud":
        return "scsearch10:"
    return "ytsearch10:"  # Default fallback