import os
import requests


class Transcriber:
    def __init__(self):
        self.groq_key = os.environ.get("GROQ_API_KEY", "")
        self.openai_key = os.environ.get("OPENAI_API_KEY", "")

    def transcribe(self, audio_path, language="es"):
        if self.groq_key:
            return self._call_whisper(
                audio_path, language,
                "https://api.groq.com/openai/v1/audio/transcriptions",
                self.groq_key,
                "whisper-large-v3",
            )
        if self.openai_key:
            return self._call_whisper(
                audio_path, language,
                "https://api.openai.com/v1/audio/transcriptions",
                self.openai_key,
                "whisper-1",
            )
        return "", "No hay API key para STT. Configura GROQ_API_KEY (gratis) o OPENAI_API_KEY."

    def _call_whisper(self, audio_path, language, url, api_key, model):
        try:
            with open(audio_path, "rb") as f:
                r = requests.post(
                    url,
                    headers={"Authorization": "Bearer " + api_key},
                    files={"file": (os.path.basename(audio_path), f)},
                    data={"model": model, "language": language},
                    timeout=30,
                )
            r.raise_for_status()
            return r.json().get("text", ""), None
        except Exception as e:
            return "", str(e)