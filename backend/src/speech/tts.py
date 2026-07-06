import subprocess
import tempfile
import os


class TTSService:
    def __init__(self):
        self.voice = os.environ.get("TTS_VOICE", "es-CO-GonzaloNeural")

    def synthesize(self, text, voice=None):
        try:
            tmp = tempfile.mktemp(suffix=".wav")
            v = voice or self.voice
            cmd = [
                "edge-tts",
                "--voice", v,
                "--text", text,
                "--write-media", tmp
            ]
            subprocess.run(cmd, check=True, timeout=30, capture_output=True)
            with open(tmp, "rb") as f:
                audio = f.read()
            os.unlink(tmp)
            return audio, None
        except FileNotFoundError:
            return None, "edge-tts no instalado. Correr: pip install edge-tts"
        except Exception as e:
            return None, str(e)