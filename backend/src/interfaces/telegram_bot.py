import threading
import telebot


def start_telegram_bot(token, runtime):
    bot = telebot.TeleBot(token)

    @bot.message_handler(commands=["start"])
    def handle_start(message):
        bot.reply_to(message, "Hola! Soy Illo, tu asistente. Escribe lo que necesites.")

    @bot.message_handler(func=lambda m: True)
    def handle_message(message):
        try:
            print("[TELEGRAM] Mensaje de " + str(message.from_user.first_name) + ": " + message.text[:60], flush=True)
            response = runtime.chat(message.text)
            if len(response) > 4000:
                for i in range(0, len(response), 4000):
                    bot.reply_to(message, response[i:i+4000])
            else:
                bot.reply_to(message, response)
            print("[TELEGRAM] Respuesta enviada OK", flush=True)
        except Exception as e:
            print("[TELEGRAM] Error: " + str(e), flush=True)
            bot.reply_to(message, "Error procesando tu mensaje. Intenta de nuevo.")

    def run_bot():
        print("[TELEGRAM] Bot iniciado, esperando mensajes...", flush=True)
        bot.infinity_polling()

    thread = threading.Thread(target=run_bot, daemon=True)
    thread.start()
    return bot
