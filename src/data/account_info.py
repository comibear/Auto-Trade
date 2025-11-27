from src.utils import setup
from hyperliquid.utils import constants

address, info, exchange = setup(
    base_url=constants.MAINNET_API_URL,
    skip_ws=True,
)
# meta, ctxs = info.meta_and_asset_ctxs()  # meta = {"universe": [...]}, ctxs = [asset data list]

# symbol = "ETH"

# for idx, asset in enumerate(meta["universe"]):
#     if asset["name"] == symbol:
#         sol_data = ctxs[idx]
#         print(f"📌 Market Data for {symbol}")
#         print(f"- Open Interest: {sol_data['openInterest']}")
#         print(f"- Mark Price: {sol_data['markPx']}")
#         print(f"- Mid Price: {sol_data['midPx']}")
#         print(f"- Oracle Price: {sol_data['oraclePx']}")
#         print(f"- Funding Rate: {sol_data['funding']}")
#         print(f"- Day Volume: {sol_data['dayNtlVlm']}")
#         print(f"- Premium: {sol_data['premium']}")
#         print(f"- Impact Prices: {sol_data['impactPxs']}")
#         break

# else:
#     print(f"⚠️ Symbol {symbol} not found in universe metadata.")

import time
symbol = "SOL"
interval = "5m"  # 예: 1m, 5m, 15m, 1h, 4h, 1d
now_ms = int(time.time() * 1000)
start_ms = now_ms - 60 * 60 * 1000 * 24 * 100 # 최근 30일

# 캔들 요청
candles = info.candles_snapshot(symbol, interval, start_ms, now_ms)

# 결과 출력
for c in candles:
    print(c)

