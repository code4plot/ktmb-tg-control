import os
import requests

BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
ALLOWED_CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])


def send_message(chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=15)
    resp.raise_for_status()