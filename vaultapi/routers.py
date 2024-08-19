import logging
import os
import pathlib
from http import HTTPStatus
from typing import Dict, List

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from vaultapi import auth, exceptions, models, rate_limit

LOGGER = logging.getLogger("uvicorn.default")
security = HTTPBearer()


async def get_secret(
    request: Request,
    filename: str,
    filepath: str | None = None,
    apikey: HTTPAuthorizationCredentials = Depends(security),
):
    """**API function to retreieve secrets.**

    **Args:**

        request: Reference to the FastAPI request object.
        filename: Filename for the secrets.
        filepath: Parent directory for the secrets.
        apikey: API Key to authenticate the request.

    **Raises:**

        APIResponse:
        Raises the HTTPStatus object with a status code and detail as response.
    """
    # TODO: convert these functions to database storage with encryption
    #   include GET and PUT
    await auth.validate(request, apikey)
    if filepath:
        secrets_file = pathlib.Path(os.path.join(filepath, filename))
    else:
        secrets_file = models.env.secrets_path.joinpath(filename)
    try:
        assert secrets_file.exists()
    except AssertionError:
        LOGGER.error("404 - %s", secrets_file)
        raise exceptions.APIResponse(
            status_code=HTTPStatus.NOT_FOUND.real, detail=f"{secrets_file!r} not found!"
        )
    rawdata = secrets_file.read_bytes()
    encrypted = models.session.fernet.encrypt(rawdata)
    raise exceptions.APIResponse(
        status_code=HTTPStatus.OK.real, detail=encrypted.decode()
    )


async def health() -> Dict[str, str]:
    """Healthcheck endpoint.

    Returns:
        Dict[str, str]:
        Returns the health response.
    """
    return {"STATUS": "OK"}


async def docs() -> RedirectResponse:
    """Redirect to docs page.

    Returns:
        RedirectResponse:
        Redirects the user to ``/docs`` page.
    """
    return RedirectResponse("/docs")


def get_all_routes() -> List[APIRoute]:
    """Get all the routes to be added for the API server.

    Returns:
        List[APIRoute]:
        Returns the routes as a list of APIRoute objects.
    """
    dependencies = [
        Depends(dependency=rate_limit.RateLimiter(each_rate_limit).init)
        for each_rate_limit in models.env.rate_limit
    ]
    routes = [
        APIRoute(path="/", endpoint=docs, methods=["GET"], include_in_schema=False),
        APIRoute(
            path="/health", endpoint=health, methods=["GET"], include_in_schema=False
        ),
        APIRoute(
            path="/get-secret",
            endpoint=get_secret,
            methods=["GET"],
            dependencies=dependencies,
        ),
    ]
    return routes
