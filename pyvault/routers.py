import logging
from http import HTTPStatus
from typing import Dict, List

from fastapi import Depends, Request
from fastapi.responses import RedirectResponse
from fastapi.routing import APIRoute
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pyvault import auth, exceptions, models, rate_limit

LOGGER = logging.getLogger("uvicorn.default")
security = HTTPBearer()


async def get_env(
    request: Request,
    apikey: HTTPAuthorizationCredentials = Depends(security),
):
    """**API function to monitor a service.**

    **Args:**

        request: Reference to the FastAPI request object.
        service_name: Name of the service to check status.
        apikey: API Key to authenticate the request.

    **Raises:**

        APIResponse:
        Raises the HTTPStatus object with a status code and detail as response.
    """
    await auth.validate(request, apikey)
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
            path="/get-env",
            endpoint=get_env,
            methods=["GET"],
            dependencies=dependencies,
        ),
    ]
    return routes
