import jwt
import hashlib
import os
import requests
import uuid
from urllib.parse import urlencode, unquote

access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']

def Order(market, side, ord_type, price=None, volume=None):
  # side {bid : 매수, ask : 매도}
  # ord_type {limit : 지정가 주문, price: 시장가 주문 (매수), market: 시장가 주문 (매도)}

  # price : 매수 시, volume : 매도 시


  params = {
    'market': market,
    'side': side,
    'ord_type': ord_type,
  }
  if price:
    params['price'] = price
  else:
    params['volume'] = volume

  query_string = unquote(urlencode(params, doseq=True)).encode("utf-8")

  m = hashlib.sha512()
  m.update(query_string)
  query_hash = m.hexdigest()

  payload = {
      'access_key': access_key,
      'nonce': str(uuid.uuid4()),
      'query_hash': query_hash,
      'query_hash_alg': 'SHA512',
  }

  jwt_token = jwt.encode(payload, secret_key)
  authorization = 'Bearer {}'.format(jwt_token)
  headers = {
    'Authorization': authorization,
  }

  res = requests.post(server_url + '/v1/orders', json=params, headers=headers)
  return res.text