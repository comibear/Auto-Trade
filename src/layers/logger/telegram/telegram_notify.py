import asyncio
from aiohttp import ClientSession

API_BASE = "https://api.telegram.org"

from dotenv import load_dotenv
load_dotenv()
import os

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token if bot_token else os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = chat_id if chat_id else os.getenv("TELEGRAM_CHAT_ID")
        self._session: ClientSession | None = None

    async def start(self):
        if not self.bot_token or not self.chat_id:
            raise RuntimeError("TELEGRAM_BOT_TOKEN/CHAT_ID 미설정")
        self._session = ClientSession()

    async def stop(self):
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def send(self, text: str):
        if self._session is None:
            raise RuntimeError("TelegramNotifier.start() 먼저 호출 필요")
        url = f"{API_BASE}/bot{self.bot_token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        async with self._session.post(url, json=payload) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Telegram send failed: {resp.status} {await resp.text()}")
