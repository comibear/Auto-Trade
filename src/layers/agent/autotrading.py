from binance_sdk_derivatives_trading_usds_futures.derivatives_trading_usds_futures import (
    DerivativesTradingUsdsFutures,
    ConfigurationWebSocketAPI,
)
from dotenv import load_dotenv
import os
load_dotenv()

configuration_ws_api = ConfigurationWebSocketAPI(
    api_key=os.getenv("HMAC_API_KEY", ""),
    api_secret=open(os.getenv("HMAC_API_SECRET", ""), "rb").read(),
    stream_url=os.getenv("STREAM_URL", DERIVATIVES_TRADING_USDS_FUTURES_WS_API_PROD_URL),
)
client = DerivativesTradingUsdsFutures(config_ws_api=configuration_ws_api)
trader = FuturesTrader(client)

if __name__ == "__main__":
    asyncio.run(trader.set_leverage("DOGEUSDT", 15))
    asyncio.run(trader.set_margin_type("DOGEUSDT", "ISOLATED"))
    asyncio.run(trader.market_buy("DOGEUSDT", qty="100"))
    
    asyncio.run(trader.place_order("DOGEUSDT", side="SELL", type="LIMIT", quantity="100", price="0.00000001", time_in_force="GTC", reduce_only=True))