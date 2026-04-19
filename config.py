import os


class Settings:
    TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
    TELEGRAM_CHAT_ID = str(os.environ["TELEGRAM_CHAT_ID"])
    TELEGRAM_WEBHOOK_SECRET = os.environ["TELEGRAM_WEBHOOK_SECRET"]
    WEBHOOK_SETUP_TOKEN = os.environ["WEBHOOK_SETUP_TOKEN"]
    PUBLIC_BASE_URL = os.environ["PUBLIC_BASE_URL"]

    BUCKET_NAME = os.environ["BUCKET_NAME"]

    PROJECT_ID = os.environ["PROJECT_ID"]
    REGION = os.environ["REGION"]
    SCHEDULER_JOB_ID = os.environ["SCHEDULER_JOB_ID"]

    CHECKER_URL = os.environ["CHECKER_URL"]