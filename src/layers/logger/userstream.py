import os
import asyncio
import json
import logging
from dotenv import load_dotenv
from aiohttp import ClientSession, ClientWebSocketResponse

from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFutures,
    DERIVATIVES_TRADING_USDS_FUTURES_WS_API_PROD_URL,
    ConfigurationWebSocketAPI,
)

from parser import FuturesEventParser
from telegram_logging import TelegramLogHandler
from telegram_notify import TelegramNotifier

load_dotenv()

# ---------- 로깅 ----------
logger = logging.getLogger("futures")
logger.setLevel(logging.INFO)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logger.addHandler(console)

notifier = TelegramNotifier(
    bot_token=os.getenv("TELEGRAM_BOT_TOKEN", ""),
    chat_id=os.getenv("TELEGRAM_CHAT_ID", "")
)
tg_handler = TelegramLogHandler(notifier)
tg_handler.setLevel(logging.INFO)
logger.addHandler(tg_handler)

# ---------- Binance SDK ----------
configuration_ws_api = ConfigurationWebSocketAPI(
    api_key=os.getenv("API_KEY", ""),
    private_key=open(os.getenv("PRIVATE_KEY_PATH", ""), "rb").read(),
    private_key_passphrase=os.getenv("PASSPHRASE", ""),
    stream_url=os.getenv("STREAM_URL", DERIVATIVES_TRADING_USDS_FUTURES_WS_API_PROD_URL),
)
client = DerivativesTradingUsdsFutures(config_ws_api=configuration_ws_api)

FSTREAM_URL = "wss://fstream.binance.com/ws"

async def start_user_stream():
    """
    userDataStream.start 호출 -> listenKey 획득
    """
    conn = await client.websocket_api.create_connection()
    try:
        resp = await conn.start_user_data_stream()
        data = resp.data().to_dict() if hasattr(resp, "data") else await resp  # SDK 버전에 따라
        # 최신 문서 기준: start 시 기존 키 있으면 연장됨. :contentReference[oaicite:3]{index=3}
        listen_key = data["result"]["listenKey"]
        logger.info(f"[listenKey] {listen_key}")
        return conn, listen_key
    except Exception as e:
        logger.exception(f"start_user_stream failed: {e}")
        await conn.close()
        raise

async def keepalive_loop(conn, interval_sec=50*60):
    """
    60분 만료 전 keepalive. 문서 권장: 약 60분마다 ping. :contentReference[oaicite:4]{index=4}
    """
    while True:
        try:
            await asyncio.sleep(interval_sec)
            await conn.keepalive_user_data_stream()
            logger.info("[keepalive] user data stream ping sent")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.exception(f"[keepalive] error: {e}")
            # 재시도는 상위에서 listenKey 재생성 로직으로 처리 가능
            break

async def consume_user_stream(listen_key: str, parser: FuturesEventParser):
    """
    fstream 사용자 데이터 스트림 연결 후 메시지 소비
    """
    url = f"{FSTREAM_URL}/{listen_key}"
    session: ClientSession = ClientSession()
    ws: ClientWebSocketResponse = None
    try:
        ws = await session.ws_connect(url, heartbeat=30)
        logger.info(f"[ws] connected to {url}")

        async for msg in ws:
            if msg.type == 1:  # TEXT
                try:
                    payload = json.loads(msg.data)
                    pretty = parser.handle(payload)
                    if pretty:
                        logger.info(pretty)
                except Exception as e:
                    logger.exception(f"[parser] error: {e} | raw={msg.data[:500]}")
            else:
                logger.warning(f"[ws] non-text message: {msg.type}")
    except asyncio.CancelledError:
        pass
    finally:
        if ws is not None:
            await ws.close()
        await session.close()

async def main():
    # 텔레그램 시작 (세션 열기)
    await notifier.start()

    # listenKey 시작
    conn, listen_key = await start_user_stream()
    parser = FuturesEventParser()

    # keepalive & consume 동시 실행
    keep_task = asyncio.create_task(keepalive_loop(conn))
    consume_task = asyncio.create_task(consume_user_stream(listen_key, parser))

    try:
        await consume_task  # 보통 여기서 영속 실행
    except asyncio.CancelledError:
        pass
    finally:
        # 작업 종료
        keep_task.cancel()
        with contextlib.suppress(Exception):
            await conn.close()

        await notifier.stop()

if __name__ == "__main__":
    import contextlib
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # Windows에서 signal 핸들러 대신 KeyboardInterrupt만으로 종료 처리
        pass
