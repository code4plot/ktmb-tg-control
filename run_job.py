import os
import requests
from google.auth.transport.requests import Request
from google.oauth2 import id_token

CHECKER_URL = os.environ["CHECKER_URL"]  # e.g. https://ktmb-checker-xxxx.a.run.app/check

def trigger_checker_service() -> str:
    token = id_token.fetch_id_token(Request(), CHECKER_URL)
    resp = requests.post(
        CHECKER_URL,
        json={},
        headers={"Authorization": f"Bearer {token}"},
        timeout=300,
    )
    resp.raise_for_status()
    return "Manual check triggered."



