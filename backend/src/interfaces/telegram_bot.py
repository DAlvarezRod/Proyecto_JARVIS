import os
import io
import tempfile
import threading
import telebot


def start_telegram_bot(token, runtime):
    bot = telebot.TeleBot(token)

    transcriber = None
    if os.environ.get("GROQ_API_KEY", "") or os.environ.get("OPENAI_API_KEY", ""):
        from src.speech.transcriber import Transcriber
        transcriber = Transcriber()
        print("[TELEGRAM] STT habilitado", flush=True)

    tts = None
    if os.environ.get("GROQ_API_KEY", ""):
        from src.speech.tts import TTSService
        tts = TTSService()
        print("[TELEGRAM] TTS habilitado", flush=True)

    @bot.message_handler(content_types=["voice", "audio"])
    def handle_voice(message):
        if not transcriber:
            bot.reply_to(message, "STT no configurado. Necesito GROQ_API_KEY o OPENAI_API_KEY.")
            return
        try:
            file_id = message.voice.file_id if message.voice else message.audio.file_id
            file_info = bot.get_file(file_id)
            downloaded = bot.download_file(file_info.file_path)

            with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as f:
                f.write(downloaded)
                temp_path = f.name

            text, error = transcriber.transcribe(temp_path)
            os.unlink(temp_path)

            if error:
                bot.reply_to(message, "Error STT: " + error)
                return
            if not text or not text.strip():
                bot.reply_to(message, "No pude entender el audio.")
                return

            bot.reply_to(message, "Escuche: " + text)
            response = runtime.chat(text)
            bot.send_message(message.chat.id, response)

            if tts:
                try:
                    audio, tts_error = tts.synthesize(response)
                    if audio and not tts_error:
                        bot.send_voice(message.chat.id, io.BytesIO(audio))
                except Exception as e:
                    print("[TELEGRAM] TTS error: " + str(e), flush=True)

        except Exception as e:
            bot.reply_to(message, "Error: " + str(e))

    @bot.message_handler(func=lambda m: True)
    def handle_message(message):
        response = runtime.chat(message.text)
        bot.reply_to(message, response)

    def run_bot():
        while True:
            try:
                bot.infinity_polling()
            except Exception as e:
                print("[TELEGRAM] Error: " + str(e) + " - reconectando...", flush=True)

    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    return bot