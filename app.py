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


async def _ptb_init_once() -> None:
    if not getattr(ptb_app, "_initialized_for_webhook", False):
        await ptb_app.initialize()
        ptb_app._initialized_for_webhook = True


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
        await _ptb_init_once()
        await ptb_app.bot.set_webhook(
            url=webhook_url,
            secret_token=TELEGRAM_WEBHOOK_SECRET,
        )

    asyncio.run(_setup())

    return jsonify({
        "ok": True,
        "webhook_url": webhook_url,
    }), 200


@app.get("/webhook-info")
def webhook_info():
    token = request.args.get("token", "")
    if token != WEBHOOK_SETUP_TOKEN:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    async def _info():
        await _ptb_init_once()
        info = await ptb_app.bot.get_webhook_info()
        return {
            "url": info.url,
            "has_custom_certificate": info.has_custom_certificate,
            "pending_update_count": info.pending_update_count,
            "last_error_date": str(info.last_error_date) if info.last_error_date else None,
            "last_error_message": info.last_error_message,
        }

    result = asyncio.run(_info())
    return jsonify({"ok": True, "telegram_result": result}), 200


@app.post("/telegram/webhook")
def telegram_webhook():
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret != TELEGRAM_WEBHOOK_SECRET:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    update_json = request.get_json(force=True)

    async def _process():
        await _ptb_init_once()
        update = Update.de_json(update_json, ptb_app.bot)
        await ptb_app.process_update(update)

    asyncio.run(_process())
    return jsonify({"ok": True}), 200