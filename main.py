import asyncio
import os

from functions_framework import http
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
)
from telegram import Update


@http
def telegram_bot(request):
    return asyncio.run(main(request))


async def main(request):
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(token).build()
    bot = app.bot

    app.add_handler(CommandHandler("start", on_start))
    app.add_handler(MessageHandler(filters.TEXT, on_message))

    if request.method == 'GET':
        await bot.set_webhook(f'https://{request.host}/telegram_bot')
        return "webhook set"

    async with app:
        update = Update.de_json(request.json, bot)
        await app.process_update(update)

    return "ok"


async def on_start(update: Update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Hello, I'm your first bot!"
    )


async def on_message(update: Update, context):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=update.message.text
    )

# import os
# from flask import Flask, request, jsonify

# from scheduler import pause_scheduler_job, resume_scheduler_job
# from storage import load_config, save_config, load_runtime_status
# from run_job import trigger_checker_service


# app = Flask(__name__)

# ALLOWED_STATIONS = {"JB SENTRAL", "WOODLANDS CIQ"}


# def format_status(cfg: dict, runtime: dict) -> str:
#     trains = runtime.get("last_available_trains", [])
#     trains_text = "\n".join(
#         f"- {t.get('departure_time', '?')} ({t.get('seats', 0)} seats)"
#         for t in trains
#     ) if trains else "None"

#     return (
#         f"enabled: {cfg.get('enabled')}\n"
#         f"force_run_once: {cfg.get('force_run_once')}\n"
#         f"is_running: {runtime.get('is_running')}\n"
#         f"run_started_at: {runtime.get('run_started_at') or '-'}\n"
#         f"route: {cfg.get('origin')} -> {cfg.get('destination')}\n"
#         f"date: {cfg.get('travel_date')}\n"
#         f"time range: {cfg.get('preferred_time_start')}-{cfg.get('preferred_time_end')}\n\n"
#         f"last_check_time: {runtime.get('last_check_time') or '-'}\n"
#         f"last_check_success: {runtime.get('last_check_success')}\n"
#         f"last_check_message: {runtime.get('last_check_message') or '-'}\n"
#         f"last_available: {runtime.get('last_available')}\n"
#         f"last_available_trains:\n{trains_text}\n"
#         f"last_alert_time: {runtime.get('last_alert_time') or '-'}\n"
#         f"last_error: {runtime.get('last_error') or '-'}"
#     )


# def handle_command(text: str) -> str:
#     cfg = load_config()
#     text = text.strip()

#     if text == "/help":
#         return (
#             "/status\n/showconfig\n/on\n/off\n/checknow\n"
#             "/setdate YYYY-MM-DD\n/settime HHMM HHMM\n"
#             "/setroute ORIGIN | DESTINATION"
#         )

#     if text == "/showconfig":
#         return str(cfg)

#     if text == "/status":
#         return format_status(cfg, load_runtime_status())

#     if text == "/on":
#         cfg["enabled"] = True
#         cfg["force_run_once"] = False
#         save_config(cfg)
#         resume_scheduler_job()
#         return "Checker enabled and scheduler resumed."

#     if text == "/off":
#         cfg["enabled"] = False
#         cfg["force_run_once"] = False
#         save_config(cfg)
#         pause_scheduler_job()
#         return "Checker disabled and scheduler paused."

#     if text == "/checknow":
#         runtime = load_runtime_status()
#         if runtime.get("is_running"):
#             started = runtime.get("run_started_at") or "unknown time"
#             return f"Checker is already running since {started}."

#         cfg["force_run_once"] = True
#         save_config(cfg)
#         trigger_checker_service()
#         return "Manual one-time check triggered."

#     if text.startswith("/setdate "):
#         cfg["travel_date"] = text.split(maxsplit=1)[1].strip()
#         save_config(cfg)
#         return f"Saved travel_date={cfg['travel_date']}"

#     if text.startswith("/settime "):
#         parts = text.split()
#         if len(parts) != 3:
#             return "Usage: /settime HHMM HHMM"
#         cfg["preferred_time_start"] = parts[1]
#         cfg["preferred_time_end"] = parts[2]
#         save_config(cfg)
#         return f"Saved preferred time range: {parts[1]}-{parts[2]}"

#     if text.startswith("/setroute "):
#         payload = text[len("/setroute "):].strip()
#         if "|" not in payload:
#             return "Usage: /setroute ORIGIN | DESTINATION"
#         origin, destination = [x.strip().upper() for x in payload.split("|", 1)]
#         if origin not in ALLOWED_STATIONS or destination not in ALLOWED_STATIONS:
#             return "Invalid station."
#         if origin == destination:
#             return "Origin and destination cannot be the same."
#         cfg["origin"] = origin
#         cfg["destination"] = destination
#         save_config(cfg)
#         return f"Saved route: {origin} -> {destination}"

#     return "Unknown command. Send /help."


# @app.post("/telegram/webhook")
# def telegram_webhook():
#     update = request.get_json(force=True)
#     message = update.get("message") or {}
#     chat = message.get("chat") or {}
#     chat_id = str(chat.get("id", ""))
#     text = message.get("text", "")

#     if not text:
#         return jsonify({"ok": True})

#     if chat_id != ALLOWED_CHAT_ID:
#         send_message(chat_id, "Unauthorized.")
#         return jsonify({"ok": True})

#     try:
#         reply = handle_command(text)
#     except Exception as e:
#         reply = f"Failed: {type(e).__name__}: {e}"

#     send_message(chat_id, reply)
#     return jsonify({"ok": True})