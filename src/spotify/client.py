import requests
from src.utils.cache import cache_res
from config.settings import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET


class SpotifyAPI:
    """
    A reusable client for interacting with the Spotify API.
    Handles authentication and provides methods for querying tracks, playlists, and more.
    """

    TOKEN_URL = "https://accounts.spotify.com/api/token"
    SEARCH_URL = "https://api.spotify.com/v1/search"

    def __init__(self):
        self.token = self.get_access_token()

    @cache_res(ttl=3600)
    def get_access_token(self):
        """
        Fetches an OAuth access token using the Client Credentials flow.
        """
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": SPOTIFY_CLIENT_ID,
            "client_secret": SPOTIFY_CLIENT_SECRET,
        }
        response = requests.post(self.TOKEN_URL, headers=headers, data=data)
        response.raise_for_status()
        return response.json().get("access_token")

    def search(self, query, search_type="track", limit=10):
        """
        Searches the Spotify catalog for tracks, artists, or playlists.
        - query: The search term (e.g., track name, artist name).
        - search_type: The type of search (track, artist, playlist).
        - limit: The number of results to return (default: 10).
        """
        params = {"q": query, "type": search_type, "limit": limit}
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(self.SEARCH_URL, headers=headers, params=params)
        response.raise_for_status()
        return response.json()


if __name__ == "__main__":
    spotify = SpotifyAPI()

    print("Searching for tracks...")
    track_results = spotify.search("Imagine", search_type="track")
    for track in track_results["tracks"]["items"]:
        print(f"{track['name']} by {track['artists'][0]['name']}")

    print("\nSearching for playlists...")
    playlist_results = spotify.search("Chill Vibes", search_type="playlist")
    for playlist in playlist_results["playlists"]["items"]:
        if playlist is not None:
            owner = playlist.get("owner", {})
            owner_name = owner.get("display_name", "Unknown Owner")
            print(f"{playlist.get('name', 'Unknown Playlist')} by {owner_name}")
