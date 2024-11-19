import requests

def Ticker(markets):
  server_url = "https://api.upbit.com"

  params = {
      "markets": markets, #"KRW-BTC,KRW-ETH"
  }

  res = requests.get(server_url + "/v1/ticker", params=params)
  return res.json()


def TickerAll(currencies):
  server_url = "https://api.upbit.com"

  params = {
      "quote_currencies": currencies, # "KRW,BTC"
  }

  res = requests.get(server_url + "/v1/ticker/all", params=params)
  return res.json()