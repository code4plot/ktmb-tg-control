from flask import Flask

from config import Settings
from ptb_runtime import PTBRuntime
from routes import bp


def create_app() -> Flask:
    app = Flask(__name__)

    ptb_runtime = PTBRuntime(Settings.TELEGRAM_BOT_TOKEN)
    app.extensions["ptb_runtime"] = ptb_runtime

    app.register_blueprint(bp)

    return app


app = create_app()