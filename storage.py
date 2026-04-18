import json
import os
from typing import Any

from google.cloud import storage

BUCKET_NAME = os.environ["BUCKET_NAME"]
_client = storage.Client()


def _blob(name: str):
    return _client.bucket(BUCKET_NAME).blob(name)


def download_json(name: str, default: dict[str, Any]) -> dict[str, Any]:
    blob = _blob(name)
    if not blob.exists():
        return default
    return json.loads(blob.download_as_text())


def upload_json(name: str, data: dict[str, Any]) -> None:
    _blob(name).upload_from_string(json.dumps(data, indent=2), content_type="application/json")


def load_config() -> dict[str, Any]:
    return download_json("checker/config.json", {})


def save_config(cfg: dict[str, Any]) -> None:
    upload_json("checker/config.json", cfg)


def load_runtime_status() -> dict[str, Any]:
    return download_json("runtime_status.json", {
        "is_running": False,
        "run_started_at": "",
        "last_check_time": "",
        "last_check_success": None,
        "last_check_message": "No checks have run yet.",
        "last_available": False,
        "last_available_trains": [],
        "last_alert_time": "",
        "last_error": "",
    })