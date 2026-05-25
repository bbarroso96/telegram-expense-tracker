import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from dotenv import load_dotenv

load_dotenv()

from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ConversationHandler, filters,
)
from config import config
from bot.handlers import (
    start, handle_expense, handle_type_choice,
    balance, detail, handle_detail_choice, week_detail, handle_week_choice, cancel, CHOOSING_TYPE,
)


class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

    def log_message(self, format, *args):
        pass  # silencia logs do servidor


def run_dummy_server():
    server = HTTPServer(("0.0.0.0", 10000), DummyHandler)
    server.serve_forever()


def main():
    threading.Thread(target=run_dummy_server, daemon=True).start()

    app = ApplicationBuilder().token(config.bot_token).build()

    conv_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & ~filters.COMMAND, handle_expense)],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(handle_type_choice)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("detail", detail))
    app.add_handler(CallbackQueryHandler(handle_detail_choice, pattern="^detail:"))
    app.add_handler(CommandHandler("week", week_detail))
    app.add_handler(CallbackQueryHandler(handle_week_choice, pattern="^week:"))
    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
