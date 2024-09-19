"""Module that performs transit encryption/decryption.

This allows the server to securely transmit the retrieved secret to be decrypted at the client side using the API key.
"""

import base64
import hashlib
import json
import secrets
from typing import Any, ByteString, Dict

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from . import models


def string_to_aes_key(input_string: str, key_length: int) -> ByteString:
    """Hashes the string.

    Args:
        input_string: String for which an AES hash has to be generated.
        key_length: AES key size used during encryption.

    See Also:
        AES supports three key lengths:
            - 128 bits (16 bytes)
            - 192 bits (24 bytes)
            - 256 bits (32 bytes)

    Returns:
        str:
        Return the first 16 bytes for the AES key
    """
    hash_object = hashlib.sha256(input_string.encode())
    return hash_object.digest()[:key_length]


def encrypt(payload: Dict[str, Any], url_safe: bool = True) -> ByteString | str:
    """Encrypt a message using GCM mode with 12 fresh bytes.

    Args:
        payload: Payload to be encrypted.
        url_safe: Boolean flag to perform base64 encoding to perform JSON serialization.

    Returns:
        ByteString | str:
        Returns the ciphertext as a string or bytes based on the ``url_safe`` flag.
    """
    nonce = secrets.token_bytes(12)
    encoded = json.dumps(payload).encode()
    # todo: instead of loading aes_key in memory,
    #  generate it on-demand and append a UTC time value that remains constant for at least 60s (probably env var)
    ciphertext = nonce + AESGCM(models.session.aes_key).encrypt(nonce, encoded, b"")
    if url_safe:
        return base64.b64encode(ciphertext).decode("utf-8")
    return ciphertext


def decrypt(ciphertext: ByteString | str) -> Dict[str, Any]:
    """Decrypt the ciphertext.

    Raises:
        Raises ``InvalidTag`` if using wrong key or corrupted ciphertext.

    Returns:
        Dict[str, Any]:
        Returns the JSON serialized decrypted payload.
    """
    if isinstance(ciphertext, str):
        ciphertext = base64.b64decode(ciphertext)
    decrypted = AESGCM(models.session.aes_key).decrypt(
        ciphertext[:12], ciphertext[12:], b""
    )
    return json.loads(decrypted)


if __name__ == "__main__":
    encrypted = encrypt({"key": "value"})
    b64_encoded = base64.b64encode(encrypted).decode("utf-8")
    print(decrypt(b64_encoded))
