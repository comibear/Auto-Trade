import jwt
import hashlib
import os
import requests
import uuid
from urllib.parse import urlencode, unquote

access_key = os.environ['UPBIT_OPEN_API_ACCESS_KEY']
secret_key = os.environ['UPBIT_OPEN_API_SECRET_KEY']
server_url = os.environ['UPBIT_OPEN_API_SERVER_URL']

def GetAccountInfo():
  payload = {
      'access_key': access_key,
      'nonce': str(uuid.uuid4()),
  }

  jwt_token = jwt.encode(payload, secret_key)
  authorization = 'Bearer {}'.format(jwt_token)
  headers = {
    'Authorization': authorization,
  }
  params = {}

  res = requests.get(server_url + '/v1/accounts', params=params, headers=headers)
  return res.json()