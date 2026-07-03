import subprocess
import ctypes
import time
import os
from typing import Any, Dict, List

from .base import Tool


class MediaTool(Tool):
    name = "media"
    description = "Control music and media playback"

    def __init__(self):
        self._sp = None

    def _get_spotify(self):
        if self._sp:
            try:
                self._sp.current_user()
                return self._sp
            except Exception:
                self._sp = None
        cid = os.environ.get("SPOTIFY_CLIENT_ID", "")
        secret = os.environ.get("SPOTIFY_CLIENT_SECRET", "")
        if not cid or not secret:
            return None
        try:
            import spotipy
            from spotipy.oauth2 import SpotifyOAuth
            auth = SpotifyOAuth(
                client_id=cid,
                client_secret=secret,
                redirect_uri="https://example.com/callback",
                scope="user-modify-playback-state user-read-playback-state user-read-currently-playing",
                cache_path=r"C:\Proyectos\Jarvis\backend\data\.spotify_cache",
                open_browser=False,
            )
            token = auth.get_cached_token()
            if not token:
                return None
            self._sp = spotipy.Spotify(auth_manager=auth)
            return self._sp
        except Exception as e:
            print("[MEDIA] Spotify error: " + str(e), flush=True)
            return None

    def get_definitions(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "media_play_pause",
                "description": "Alterna entre reproducir y pausar la musica",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "media_next",
                "description": "Salta a la siguiente cancion",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "media_previous",
                "description": "Vuelve a la cancion anterior",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "media_play_search",
                "description": "Busca y reproduce un artista, cancion o album en Spotify",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Nombre del artista, cancion o album"},
                        "type": {"type": "string", "description": "Tipo: track, artist, album, playlist. Default: track"},
                    },
                    "required": ["query"],
                },
            },
            {
                "name": "media_volume",
                "description": "Ajusta el volumen de Spotify de 0 a 100",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "integer", "description": "Nivel de volumen de 0 a 100"},
                    },
                    "required": ["level"],
                },
            },
            {
                "name": "media_system_volume",
                "description": "Ajusta el volumen general del sistema de 0 a 100",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "level": {"type": "integer", "description": "Nivel de volumen de 0 a 100"},
                    },
                    "required": ["level"],
                },
            },
            {
                "name": "media_mute",
                "description": "Silencia o des-silencia el audio",
                "parameters": {"type": "object", "properties": {}},
            },
            {
                "name": "media_now_playing",
                "description": "Muestra la cancion que esta sonando en Spotify",
                "parameters": {"type": "object", "properties": {}},
            },
        ]

    def _send_key(self, vk_code):
        ctypes.windll.user32.keybd_event(vk_code, 0, 0x0001, 0)
        ctypes.windll.user32.keybd_event(vk_code, 0, 0x0003, 0)

    def execute(self, function_name, arguments):
        sp = self._get_spotify()

        if function_name == "media_play_pause":
            if sp:
                try:
                    pb = sp.current_playback()
                    if pb and pb.get("is_playing"):
                        sp.pause_playback()
                        return "Musica pausada"
                    else:
                        sp.start_playback()
                        return "Musica reproduciendo"
                except Exception:
                    pass
            self._send_key(0xB3)
            return "Play/Pause enviado"

        elif function_name == "media_next":
            if sp:
                try:
                    sp.next_track()
                    time.sleep(0.5)
                    current = sp.current_playback()
                    if current and current.get("item"):
                        name = current["item"].get("name", "")
                        artist = current["item"].get("artists", [{}])[0].get("name", "")
                        return "Siguiente: " + name + " - " + artist
                except Exception:
                    pass
            self._send_key(0xB0)
            return "Siguiente track"

        elif function_name == "media_previous":
            if sp:
                try:
                    sp.previous_track()
                    return "Track anterior"
                except Exception:
                    pass
            self._send_key(0xB1)
            return "Track anterior"

        elif function_name == "media_play_search":
            query = arguments.get("query", "")
            search_type = arguments.get("type", "track")
            if not query:
                return "Error: query vacia"
            if not sp:
                return "Error: Spotify no autorizado. Ejecutar auth_spotify.py primero."
            try:
                results = sp.search(q=query, type=search_type, limit=5)
                key = search_type + "s"
                items = results.get(key, {}).get("items", [])
                if not items:
                    return "No se encontro: " + query
                item = items[0]
                name = item.get("name", "")
                uri = item.get("uri", "")
                if search_type == "track":
                    artist = item.get("artists", [{}])[0].get("name", "")
                    sp.start_playback(uris=[uri])
                    return "Reproduciendo: " + name + " de " + artist
                elif search_type == "artist":
                    sp.start_playback(context_uri=uri)
                    return "Reproduciendo artista: " + name
                elif search_type in ("album", "playlist"):
                    sp.start_playback(context_uri=uri)
                    return "Reproduciendo " + search_type + ": " + name
                else:
                    sp.start_playback(uris=[uri])
                    return "Reproduciendo: " + name
            except Exception as e:
                err = str(e)
                if "Premium" in err or "PREMIUM" in err:
                    return "Error: se requiere Spotify Premium para controlar la reproduccion desde la API"
                return "Error: " + err

        elif function_name == "media_volume":
            level = max(0, min(100, arguments.get("level", 50)))
            if sp:
                try:
                    sp.volume(level)
                    return "Volumen de Spotify ajustado a " + str(level) + "%"
                except Exception as e:
                    return "Error: " + str(e)
            return "Error: Spotify no conectado"

        elif function_name == "media_system_volume":
            level = max(0, min(100, arguments.get("level", 50)))
            try:
                for _ in range(50):
                    self._send_key(0xAE)
                time.sleep(0.3)
                steps = level // 2
                for _ in range(steps):
                    self._send_key(0xAF)
                return "Volumen del sistema ajustado a " + str(level) + "%"
            except Exception as e:
                return "Error: " + str(e)

        elif function_name == "media_mute":
            self._send_key(0xAD)
            return "Mute/Unmute enviado"

        elif function_name == "media_now_playing":
            if sp:
                try:
                    current = sp.current_playback()
                    if current and current.get("item"):
                        item = current["item"]
                        name = item.get("name", "")
                        artist = item.get("artists", [{}])[0].get("name", "")
                        album = item.get("album", {}).get("name", "")
                        progress = current.get("progress_ms", 0) // 1000
                        duration = item.get("duration_ms", 0) // 1000
                        playing = "Reproduciendo" if current.get("is_playing") else "Pausado"
                        vol = current.get("device", {}).get("volume_percent", "?")
                        return (
                            playing + ": " + name + " - " + artist
                            + "\nAlbum: " + album
                            + "\nTiempo: " + str(progress // 60) + ":" + str(progress % 60).zfill(2)
                            + " / " + str(duration // 60) + ":" + str(duration % 60).zfill(2)
                            + "\nVolumen Spotify: " + str(vol) + "%"
                        )
                    return "No hay nada reproduciendose en Spotify"
                except Exception:
                    pass
            return "No se pudo obtener info de reproduccion"

        return "Funcion no encontrada"
