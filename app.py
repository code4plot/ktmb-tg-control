import asyncio
import os

from flask import Flask, jsonify, request
from telegram import Update

from bot import build_application

app = Flask(__name__)

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
PUBLIC_BASE_URL = os.environ["PUBLIC_BASE_URL"]
WEBHOOK_SETUP_TOKEN = os.environ["WEBHOOK_SETUP_TOKEN"]
TELEGRAM_WEBHOOK_SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]

ptb_app = build_application(BOT_TOKEN)
_ptb_initialized = False
_ptb_init_lock = asyncio.Lock()


async def _init_ptb_once() -> None:
    global _ptb_initialized

    if _ptb_initialized:
        return

    async with _ptb_init_lock:
        if _ptb_initialized:
            return
        await ptb_app.initialize()
        _ptb_initialized = True


@app.get("/health")
def health():
    return jsonify({"ok": True}), 200


@app.get("/setup-webhook")
def setup_webhook():
    token = request.args.get("token", "")
    if token != WEBHOOK_SETUP_TOKEN:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    webhook_url = f"{PUBLIC_BASE_URL}/telegram/webhook"

    async def _setup():
        await _init_ptb_once()
        await ptb_app.bot.set_webhook(
            url=webhook_url,
            secret_token=TELEGRAM_WEBHOOK_SECRET,
        )

    asyncio.run(_setup())

    return jsonify({
        "ok": True,
        "webhook_url": webhook_url,
        "message": "Telegram webhook registered."
    }), 200


@app.get("/webhook-info")
def webhook_info():
    token = request.args.get("token", "")
    if token != WEBHOOK_SETUP_TOKEN:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    async def _info():
        await _init_ptb_once()
        info = await ptb_app.bot.get_webhook_info()
        return {
            "url": info.url,
            "pending_update_count": info.pending_update_count,
            "last_error_message": info.last_error_message,
        }

    return jsonify({"ok": True, "telegram_result": asyncio.run(_info())}), 200


@app.post("/telegram/webhook")
def telegram_webhook():
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret != TELEGRAM_WEBHOOK_SECRET:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    update_json = request.get_json(force=True)

    async def _process():
        await _init_ptb_once()
        update = Update.de_json(update_json, ptb_app.bot)
        await ptb_app.process_update(update)

    asyncio.run(_process())
    return jsonify({"ok": True}), 200