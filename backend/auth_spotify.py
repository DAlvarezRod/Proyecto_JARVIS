import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.environ.get("SPOTIFY_CLIENT_ID"),
    client_secret=os.environ.get("SPOTIFY_CLIENT_SECRET"),
    redirect_uri="https://example.com/callback",
    scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
    cache_path=r"C:\Proyectos\Jarvis\backend\data\.spotify_cache",
    open_browser=True,
))

user = sp.current_user()
print("Conectado como: " + user["display_name"])
print("Autorizacion guardada!")
