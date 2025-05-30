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
    TRACK_URL = "https://api.spotify.com/v1/tracks"

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

    def get_track(self, track_id):
        """
        Fetches information about a specific track by its track_id.
        - track_id: The Spotify ID of the track.
        """
        url = f"{self.TRACK_URL}/{track_id}"
        headers = {"Authorization": f"Bearer {self.token}"}
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        return response.json()

    @staticmethod
    def get_audio_preview_url(response: dict) -> str:
        """
        Fetches link to audiofile (audio_preview_url) from `episodes` block in callback Spotify API answer.

        :param response: JSON Spotify API .
        :return: Link to audiofile or error message.
        """
        try:
            episodes = response.get("episodes", {})
            items = episodes.get("items", [])

            if not items:
                return "❌ Нет доступных эпизодов с предпрослушиванием."

            first_episode = items[0]
            audio_preview_url = first_episode.get("audio_preview_url")

            if audio_preview_url:
                return audio_preview_url
            else:
                return "❌ У данного эпизода нет доступного предпрослушивания."
        except Exception as e:
            return f"❌ Произошла ошибка: {str(e)}"


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
