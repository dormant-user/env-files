import logging
import sqlite3
from http import HTTPStatus
from typing import Dict, List

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from . import auth, database, exceptions, models, payload, rate_limit

LOGGER = logging.getLogger("uvicorn.default")
security = HTTPBearer()


async def retrieve_existing(key: str, table_name: str) -> str | None:
    """Retrieve existing secret from database.

    Args:
        key: Name of the secret to retrieve.
        table_name: Name of the table where the secret is stored.

    Returns:
        str:
        Returns the secret value.
    """
    try:
        return database.get_secret(key=key, table_name=table_name)
    except sqlite3.OperationalError as error:
        LOGGER.error(error)
        raise exceptions.APIResponse(
            status_code=HTTPStatus.BAD_REQUEST.real, detail=error.args[0]
        )


async def get_secret(
    request: Request,
    key: str,
    table_name: str = "default",
    apikey: HTTPAuthorizationCredentials = Depends(security),
):
    """**API function to retrieve secrets.**

    **Args:**

        request: Reference to the FastAPI request object.
        key: Name of the secret to be retrieved.
        table_name: Name of the table where the secret is stored.
        apikey: API Key to authenticate the request.

    **Raises:**

        APIResponse:
        Raises the HTTPStatus object with a status code and detail as response.
    """
    await auth.validate(request, apikey)
    if value := await retrieve_existing(key, table_name):
        LOGGER.info("Secret value for '%s' was retrieved", key)
        raise exceptions.APIResponse(status_code=HTTPStatus.OK.real, detail=value)
    LOGGER.info("Secret value for '%s' NOT found in the datastore", key)
    raise exceptions.APIResponse(
        status_code=HTTPStatus.NOT_FOUND.real, detail=HTTPStatus.NOT_FOUND.phrase
    )


async def put_secret(
    request: Request,
    data: payload.PutSecret,
    apikey: HTTPAuthorizationCredentials = Depends(security),
):
    """**API function to add secrets to database.**

    **Args:**

        request: Reference to the FastAPI request object.
        data: Payload with ``key``, ``value``, and ``table_name`` as body.
        apikey: API Key to authenticate the request.

    **Raises:**

        APIResponse:
        Raises the HTTPStatus object with a status code and detail as response.
    """
    await auth.validate(request, apikey)
    if await retrieve_existing(data.key, data.table_name):
        LOGGER.info("Secret value for '%s' will be overridden", data.key)
    else:
        LOGGER.info("Storing a secret value for '%s' in the datastore", data.key)
    database.put_secret(key=data.key, value=data.value, table_name=data.table_name)
    raise exceptions.APIResponse(
        status_code=HTTPStatus.OK.real, detail=HTTPStatus.OK.phrase
    )


async def delete_secret(
    request: Request,
    data: payload.DeleteSecret,
    apikey: HTTPAuthorizationCredentials = Depends(security),
):
    """**API function to delete secrets from database.**

    **Args:**

        request: Reference to the FastAPI request object.
        data: Payload with ``key`` and ``table_name`` as body.
        apikey: API Key to authenticate the request.

    **Raises:**

        APIResponse:
        Raises the HTTPStatus object with a status code and detail as response.
    """
    await auth.validate(request, apikey)
    if await retrieve_existing(data.key, data.table_name):
        LOGGER.info("Secret value for '%s' will be removed", data.key)
    else:
        LOGGER.warning("Secret value for '%s' NOT found", data.key)
        raise exceptions.APIResponse(
            status_code=HTTPStatus.NOT_FOUND.real, detail=HTTPStatus.NOT_FOUND.phrase
        )
    database.remove_secret(key=data.key, table_name=data.table_name)
    raise exceptions.APIResponse(
        status_code=HTTPStatus.OK.real, detail=HTTPStatus.OK.phrase
    )


async def create_table(
    request: Request,
    table_name: str,
    apikey: HTTPAuthorizationCredentials = Depends(security),
):
    """**API function to create a new table in the database.**

    **Args:**

        request: Reference to the FastAPI request object.
        table_name: Name of the table to be created.
        apikey: API Key to authenticate the request.

    **Raises:**

        APIResponse:
        Raises the HTTPStatus object with a status code and detail as response.
    """
    await auth.validate(request, apikey)
    try:
        models.database.create_table(table_name, ["key", "value"])
    except sqlite3.OperationalError as error:
        LOGGER.error(error)
        raise exceptions.APIResponse(
            status_code=HTTPStatus.EXPECTATION_FAILED.real, detail=error.args[0]
        )
    raise exceptions.APIResponse(
        status_code=HTTPStatus.OK.real, detail=HTTPStatus.OK.phrase
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
        APIRoute(
            path="/put-secret",
            endpoint=put_secret,
            methods=["POST"],
            dependencies=dependencies,
        ),
        APIRoute(
            path="/delete-secret",
            endpoint=delete_secret,
            methods=["DELETE"],
            dependencies=dependencies,
        ),
        APIRoute(
            path="/create-table",
            endpoint=create_table,
            methods=["POST"],
            dependencies=dependencies,
        ),
    ]
    return routes
