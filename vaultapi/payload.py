from typing import Dict

from pydantic import BaseModel


class DeleteSecret(BaseModel):
    """Payload for delete-secret API call.

    >>> DeleteSecret

    """

    key: str
    table_name: str = "default"


class PutSecret(BaseModel):
    """Payload for put-secret API call.

    >>> PutSecret

    """

    key: str
    value: str
    table_name: str = "default"


class PutSecrets(BaseModel):
    """Payload for put-secrets API call.

    >>> PutSecret

    """

    secrets: Dict[str, str]
    table_name: str = "default"
