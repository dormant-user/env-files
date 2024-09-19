import base64
import hashlib
import json
import os
import time
from typing import Dict, ByteString, Any

import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

APIKEY = os.environ["APIKEY"]


def transit_decrypt(ciphertext: str | ByteString, key_length: int = 32) -> Dict[str, Any]:
    epoch = int(time.time()) // 60
    hash_object = hashlib.sha256(f"{epoch}.{APIKEY}".encode())
    aes_key = hash_object.digest()[:key_length]
    if isinstance(ciphertext, str):
        ciphertext = base64.b64decode(ciphertext)
    decrypted = AESGCM(aes_key).decrypt(ciphertext[:12], ciphertext[12:], b"")
    return json.loads(decrypted)


def get_cipher():
    headers = {
        'accept': 'application/json',
        'Authorization': f'Bearer {APIKEY}',
    }
    params = {
        'table_name': 'default',
    }
    response = requests.get('http://0.0.0.0:8080/get-table', params=params, headers=headers)
    assert response.ok, response.text
    return response.json()['detail']


print(transit_decrypt(ciphertext=get_cipher()))
