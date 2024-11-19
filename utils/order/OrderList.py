import jwt
import hashlib
import os
import requests
import uuid
from urllib.parse import urlencode, unquote

access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']

def GetOrderList(params={}, closed=True):

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
  
  url = server_url + '/v1/orders/closed' if closed else server_url + '/v1/orders/open'
  res = requests.get(url, params=params, headers=headers)
  
  return res.json()