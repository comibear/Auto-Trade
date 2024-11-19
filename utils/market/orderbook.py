import requests

def OrderBook(markets, level=0):

  url = "https://api.upbit.com/v1/orderbook?" + f"markets={markets}" + f"&level={level}"

  headers = {"accept": "application/json"}

  response = requests.get(url, headers=headers)

  return response.text