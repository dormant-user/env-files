import logging
import secrets
import time
from http import HTTPStatus

from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import exceptions, models

LOGGER = logging.getLogger("uvicorn.default")
EPOCH = lambda: int(time.time())  # noqa: E731
SECURITY = HTTPBearer()


async def validate(request: Request, apikey: HTTPAuthorizationCredentials) -> None:
    """Validates the auth request using HTTPBearer.

    Args:
        request: Takes the authorization header token as an argument.
        apikey: Basic APIKey required for all the routes.

    Raises:
        APIResponse:
        - 401: If authorization is invalid.
        - 403: If host address is forbidden.
    """
    if apikey.credentials.startswith("\\"):
        auth = bytes(apikey.credentials, "utf-8").decode(encoding="unicode_escape")
    else:
        auth = apikey.credentials
    if secrets.compare_digest(auth, models.env.apikey):
        LOGGER.info(
            "Connection received from client-host: %s, host-header: %s, x-fwd-host: %s",
            request.client.host,
            request.headers.get("host"),
            request.headers.get("x-forwarded-host"),
        )
        if user_agent := request.headers.get("user-agent"):
            LOGGER.info("User agent: %s", user_agent)
        return
    raise exceptions.APIResponse(
        status_code=HTTPStatus.UNAUTHORIZED.real, detail=HTTPStatus.UNAUTHORIZED.phrase
    )
