import asyncio
import concurrent.futures
import threading

from bot import build_application


class PTBRuntime:
    def __init__(self, bot_token: str):
        self._bot_token = bot_token
        self._application = build_application(bot_token)

        self._loop = None
        self._thread = None

        self._initialized = False
        self._init_lock = threading.Lock()

    @property
    def application(self):
        return self._application

    @property
    def bot(self):
        return self._application.bot

    def _event_loop_thread(self, loop: asyncio.AbstractEventLoop) -> None:
        asyncio.set_event_loop(loop)
        loop.run_forever()

    def ensure_loop(self) -> asyncio.AbstractEventLoop:
        if self._loop and self._loop.is_running():
            return self._loop

        loop = asyncio.new_event_loop()
        thread = threading.Thread(
            target=self._event_loop_thread,
            args=(loop,),
            daemon=True,
            name="ptb-event-loop",
        )
        thread.start()

        self._loop = loop
        self._thread = thread
        return self._loop

    def run_coro(self, coro, timeout: float = 30):
        loop = self.ensure_loop()
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result(timeout=timeout)

    def initialize_once(self) -> None:
        if self._initialized:
            return

        with self._init_lock:
            if self._initialized:
                return
            self.run_coro(self._application.initialize(), timeout=60)
            self._initialized = True

    def process_update_json(self, update_json: dict, timeout: float = 60) -> None:
        from telegram import Update

        self.initialize_once()

        async def _process():
            update = Update.de_json(update_json, self.bot)
            await self._application.process_update(update)

        self.run_coro(_process(), timeout=timeout)

    def set_webhook(self, url: str, secret_token: str, timeout: float = 30) -> None:
        self.initialize_once()

        async def _set():
            await self.bot.set_webhook(url=url, secret_token=secret_token)

        self.run_coro(_set(), timeout=timeout)

    def get_webhook_info(self, timeout: float = 30) -> dict:
        self.initialize_once()

        async def _info():
            info = await self.bot.get_webhook_info()
            return {
                "url": info.url,
                "pending_update_count": info.pending_update_count,
                "last_error_message": info.last_error_message,
            }

        return self.run_coro(_info(), timeout=timeout)