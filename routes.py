import concurrent.futures

from flask import Blueprint, current_app, jsonify, request

from config import Settings

bp = Blueprint("main", __name__)


@bp.get("/health")
def health():
    return jsonify({"ok": True}), 200


@bp.get("/setup-webhook")
def setup_webhook():
    token = request.args.get("token", "")
    if token != Settings.WEBHOOK_SETUP_TOKEN:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    webhook_url = f"{Settings.PUBLIC_BASE_URL}/telegram/webhook"
    ptb_runtime = current_app.extensions["ptb_runtime"]
    ptb_runtime.set_webhook(
        url=webhook_url,
        secret_token=Settings.TELEGRAM_WEBHOOK_SECRET,
    )

    return jsonify({
        "ok": True,
        "webhook_url": webhook_url,
        "message": "Telegram webhook registered."
    }), 200


@bp.get("/webhook-info")
def webhook_info():
    token = request.args.get("token", "")
    if token != Settings.WEBHOOK_SETUP_TOKEN:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    ptb_runtime = current_app.extensions["ptb_runtime"]
    info = ptb_runtime.get_webhook_info()

    return jsonify({
        "ok": True,
        "telegram_result": info,
    }), 200


@bp.post("/telegram/webhook")
def telegram_webhook():
    secret = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
    if secret != Settings.TELEGRAM_WEBHOOK_SECRET:
        return jsonify({"ok": False, "message": "Unauthorized"}), 401

    update_json = request.get_json(force=True)
    ptb_runtime = current_app.extensions["ptb_runtime"]

    try:
        ptb_runtime.process_update_json(update_json, timeout=60)
    except concurrent.futures.TimeoutError:
        return jsonify({"ok": False, "message": "Processing timed out"}), 504

    return jsonify({"ok": True}), 200