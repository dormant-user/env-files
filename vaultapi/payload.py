from pydantic import BaseModel


class DeleteSecret(BaseModel):
    """Payload for delete-secret API call.

    >>> DeleteSecret

    """

    key: str
    table_name: str = "default"


class PutSecret(BaseModel):
    """Payload for put-secret API call.

    >>> DeleteSecret

    """

    key: str
    value: str
    table_name: str = "default"
