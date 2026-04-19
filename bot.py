import re

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from storage import load_config, save_config, load_runtime_status
from scheduler import pause_scheduler_job, resume_scheduler_job
from run_job import trigger_checker_service
from config import Settings
from datetime import datetime

ALLOWED_STATIONS = {"JB SENTRAL", "WOODLANDS CIQ"}


def validate_date(date_str: str) -> bool:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_hhmm(value: str) -> bool:
    if not re.fullmatch(r"\d{4}", value):
        return False
    hh = int(value[:2])
    mm = int(value[2:])
    return 0 <= hh <= 23 and 0 <= mm <= 59


def format_status(cfg: dict, runtime: dict) -> str:
    trains = runtime.get("last_available_trains", [])
    trains_text = "\n".join(
        f"- {t.get('departure_time', '?')} ({t.get('seats', 0)} seats)"
        for t in trains
    ) if trains else "None"

    return (
        f"enabled: {cfg.get('enabled')}\n"
        f"force_run_once: {cfg.get('force_run_once')}\n"
        f"is_running: {runtime.get('is_running')}\n"
        f"run_started_at: {runtime.get('run_started_at') or '-'}\n"
        f"route: {cfg.get('origin')} -> {cfg.get('destination')}\n"
        f"date: {cfg.get('travel_date')}\n"
        f"time range: {cfg.get('preferred_time_start')}-{cfg.get('preferred_time_end')}\n\n"
        f"last_check_time: {runtime.get('last_check_time') or '-'}\n"
        f"last_check_success: {runtime.get('last_check_success')}\n"
        f"last_check_message: {runtime.get('last_check_message') or '-'}\n"
        f"last_available: {runtime.get('last_available')}\n"
        f"last_available_trains:\n{trains_text}\n"
        f"last_alert_time: {runtime.get('last_alert_time') or '-'}\n"
        f"last_error: {runtime.get('last_error') or '-'}"
    )


async def allowed(update: Update) -> bool:
    chat_id = str(update.effective_chat.id) if update.effective_chat else ""
    if chat_id != Settings.TELEGRAM_CHAT_ID:
        if update.effective_message:
            await update.effective_message.reply_text("Unauthorized.")
        return False
    return True


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return
    await update.effective_message.reply_text(
        "/status\n"
        "/showconfig\n"
        "/on\n"
        "/off\n"
        "/checknow\n"
        "/setdate YYYY-MM-DD\n"
        "/settime HHMM HHMM\n"
        "/setroute ORIGIN | DESTINATION"
    )


async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return
    await update.effective_message.reply_text(
        format_status(load_config(), load_runtime_status())
    )


async def showconfig_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return
    await update.effective_message.reply_text(str(load_config()))


async def on_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return
    cfg = load_config()
    cfg["enabled"] = True
    cfg["force_run_once"] = False
    save_config(cfg)
    resume_scheduler_job()
    await update.effective_message.reply_text("Checker enabled and scheduler resumed.")


async def off_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return
    cfg = load_config()
    cfg["enabled"] = False
    cfg["force_run_once"] = False
    save_config(cfg)
    pause_scheduler_job()
    await update.effective_message.reply_text("Checker disabled and scheduler paused.")


async def checknow_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return

    runtime = load_runtime_status()
    if runtime.get("is_running"):
        started = runtime.get("run_started_at") or "unknown time"
        await update.effective_message.reply_text(
            f"Checker is already running since {started}."
        )
        return

    cfg = load_config()
    cfg["force_run_once"] = True
    save_config(cfg)
    trigger_checker_service()
    await update.effective_message.reply_text("Manual one-time check triggered.")


async def setdate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return

    if len(context.args) != 1:
        await update.effective_message.reply_text("Usage: /setdate YYYY-MM-DD")
        return

    date_str = context.args[0].strip()
    if not validate_date(date_str):
        await update.effective_message.reply_text("Invalid date. Use YYYY-MM-DD.")
        return

    cfg = load_config()
    cfg["travel_date"] = date_str
    save_config(cfg)

    await update.effective_message.reply_text(f"Saved travel_date={date_str}")


async def settime_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return

    if len(context.args) != 2:
        await update.effective_message.reply_text("Usage: /settime HHMM HHMM")
        return

    start = context.args[0].strip()
    end = context.args[1].strip()

    if not validate_hhmm(start) or not validate_hhmm(end):
        await update.effective_message.reply_text(
            "Invalid time. Use HHMM HHMM, for example 1800 2200."
        )
        return

    cfg = load_config()
    cfg["preferred_time_start"] = start
    cfg["preferred_time_end"] = end
    save_config(cfg)

    await update.effective_message.reply_text(
        f"Saved preferred time range: {start}-{end}"
    )


async def setroute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await allowed(update):
        return

    raw_text = update.effective_message.text or ""
    payload = raw_text[len("/setroute"):].strip()

    if "|" not in payload:
        await update.effective_message.reply_text(
            "Usage: /setroute ORIGIN | DESTINATION"
        )
        return

    origin, destination = [x.strip().upper() for x in payload.split("|", 1)]

    if not origin or not destination:
        await update.effective_message.reply_text(
            "Origin and destination cannot be empty."
        )
        return

    if origin not in ALLOWED_STATIONS or destination not in ALLOWED_STATIONS:
        await update.effective_message.reply_text(
            "Invalid station. Allowed values:\n"
            + "\n".join(sorted(ALLOWED_STATIONS))
        )
        return

    if origin == destination:
        await update.effective_message.reply_text(
            "Origin and destination cannot be the same."
        )
        return

    cfg = load_config()
    cfg["origin"] = origin
    cfg["destination"] = destination
    save_config(cfg)

    await update.effective_message.reply_text(
        f"Saved route: {origin} -> {destination}"
    )


def build_application(bot_token: str) -> Application:
    application = Application.builder().token(bot_token).build()

    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("status", status_cmd))
    application.add_handler(CommandHandler("showconfig", showconfig_cmd))
    application.add_handler(CommandHandler("on", on_cmd))
    application.add_handler(CommandHandler("off", off_cmd))
    application.add_handler(CommandHandler("checknow", checknow_cmd))
    application.add_handler(CommandHandler("setdate", setdate_cmd))
    application.add_handler(CommandHandler("settime", settime_cmd))
    application.add_handler(CommandHandler("setroute", setroute_cmd))

    return application