import sys
import os
import time
import pandas as pd
import json
# sys path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.account.account import GetAccountInfo
from utils.market.market import MarketInfo
from utils.market.candle import GetCandle
from utils.market.ticker import Ticker, TickerAll
from utils.helper.metrics import calculate_rsi, calculate_bollinger_bands
from utils.order.Order import Order
from utils.helper.logger import log
import config

import asyncio
from datetime import datetime

async def update_metrics(market):
  global metrics
  while True:
    try:
      candles = GetCandle(market=market, count=config.Model.candle_lags, unit="minutes")
      trade_prices = [item['trade_price'] for item in candles]
      metrics[market]["rsi"] = calculate_rsi(trade_prices[-14:])
      metrics[market]["bb"] = calculate_bollinger_bands(trade_prices)

      log(f"[{datetime.now()}] Metrics Updated {market}: RSI={metrics[market]['rsi']}, BB={metrics[market]['bb']}")
    except Exception as e:
      log(f"[{datetime.now()}] Error updating metrics: {e}")

    await asyncio.sleep(60)

def checker(market, side):
  account_info = GetAccountInfo()
  if side == 'bid':
    krw_balance = next((float(item['balance']) for item in account_info if item['currency'] == 'KRW'), 0)

    return krw_balance
  
  else:
    volume = next((float(item['balance']) for item in account_info if item['currency'] == market[4:]), 0)

    return volume

async def analyze_and_trade(market):
  global metrics
  while True:
    try:
      tick = Ticker(markets=market)
      current_price = tick[0]['trade_price']
      
      if metrics[market]["bb"] is not None and metrics[market]["rsi"] is not None:
          
        if (current_price / metrics[market]["bb"][1]) < 1.001 and metrics[market]["rsi"] < 30 and checker(market, 'bid') > 1000:
          res = Order(market=market, side="bid", ord_type='price', price=checker(market, 'bid'))
          log(res)
        
        if (current_price / metrics[market]["bb"][2]) > 0.999 and metrics[market]["rsi"] > 70 and checker(market, 'ask') >= 1:
          res = Order(market=market, side="ask", ord_type='market', volume=checker(market, 'ask'))
          log(res)

    except Exception as e:
      log(f"[{datetime.now()}] Error analyzing and trading: {e}")

    await asyncio.sleep(10)

async def main(ordered_markets):
  tasks = []
  for market in ordered_markets:
    tasks.append(update_metrics(market))
    tasks.append(analyze_and_trade(market))
  await asyncio.gather(*tasks)

if __name__ == "__main__":
  all_ticks = TickerAll("KRW")

  ordered_markets = [
    item['market']
    for item in sorted(all_ticks, key=lambda x: x['acc_trade_volume_24h'], reverse=True)
    if item['low_price'] >= 500
    ][:10] # Only for upper 10 coins

  metrics = {market: {"rsi": None, "bb": None} for market in ordered_markets}

  asyncio.run(main(ordered_markets))
