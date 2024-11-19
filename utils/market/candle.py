import requests
import json

def GetCandle(market, count, to=None, unit='seconds'):
  # KRW-BTC 마켓에 2024년 10월 1일(UTC) 이전 초봉 1개를 요청

  url = "https://api.upbit.com/v1/candles/" + unit
  if unit == "minutes":
    url += "/1"

  params = {  
      'market': market,  
      'count': count,
  }  
  if to:
    params['to'] = to

  headers = {"accept": "application/json"}

  response = requests.get(url, params=params, headers=headers)

  return json.loads(response.text)