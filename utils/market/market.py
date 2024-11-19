import requests

def MarketInfo(detailed=False):
  url = "https://api.upbit.com/v1/market/all?is_details="
  url = url + "true" if detailed else url + "false"

  headers = {"accept": "application/json"}

  res = requests.get(url, headers=headers)

  return res.json()