import base64
from typing import ByteString


def encode_secret(key: str) -> ByteString:
    """Encodes a key into URL safe string.

    Args:
        key: Key to be encoded.

    Returns:
        ByteString:
        Returns an encoded URL safe string.
    """
    return base64.urlsafe_b64encode(key.encode(encoding="UTF-8"))
