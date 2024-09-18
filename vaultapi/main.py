import logging
import pathlib

import uvicorn
from cryptography.fernet import Fernet
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import database, models, routes, squire, version

LOGGER = logging.getLogger("uvicorn.default")
VaultAPI = FastAPI(
    title="VaultAPI",
    description="Lightweight service to serve secrets and environment variables",
    version=version.__version__,
)


def __init__(**kwargs) -> None:
    """Instantiates the env, session and database connections."""
    models.env = squire.load_env(**kwargs)
    models.session.fernet = Fernet(models.env.secret)
    models.database = models.Database(models.env.database)
    default_allowed = ("0.0.0.0", "127.0.0.1", "localhost")
    if models.env.host in default_allowed:
        models.session.allowed_origins.update(default_allowed)
    else:
        models.session.allowed_origins.add(models.env.host)
    for allowed in models.env.allowed_origins:
        models.session.allowed_origins.add(allowed.host)
    for cidr_range in models.env.allowed_ip_range:
        LOGGER.info("Adding the IP range: %s to allowed_origins", cidr_range)
        ip_notion = '.'.join(cidr_range.split('.')[0:-1])
        start_ip, end_ip = cidr_range.split('.')[-1].split('-')
        start_ip, end_ip = int(start_ip), int(end_ip) + 1
        for i in range(start_ip, end_ip):
            models.session.allowed_origins.add(f"{ip_notion}.{i}")
    LOGGER.info("Allowed origins: %s", models.session.allowed_origins)


def enable_cors() -> None:
    """Enables CORS policy."""
    LOGGER.info("Setting CORS policy")
    origins = [
        "http://localhost.com",
        "https://localhost.com",
    ]
    for website in models.env.allowed_origins:
        origins.append(f"http://{website.host}")  # noqa: HttpUrlsUsage
        origins.append(f"https://{website.host}")
    VaultAPI.add_middleware(
        CORSMiddleware,  # noqa: PyTypeChecker
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=[
            # Default headers
            "host",
            "user-agent",
            "authorization",
        ],
    )


def start(**kwargs) -> None:
    """Starter function for the API, which uses uvicorn server as trigger.

    Keyword Args:
        env_file: Env filepath to load the environment variables.
        apikey: API Key to authenticate the server.
        secret: Secret access key to access the secret content.
        host: Hostname for the API server.
        port: Port number for the API server.
        workers: Number of workers for the uvicorn server.
        database: FilePath to store the auth database that handles the authentication errors.
        rate_limit: List of dictionaries with ``max_requests`` and ``seconds`` to apply as rate limit.
        log_config: Logging configuration as a dict or a FilePath. Supports .yaml/.yml, .json or .ini formats.
    """
    __init__(**kwargs)
    database.create_table("default", ["key", "value"])
    module_name = pathlib.Path(__file__)
    enable_cors()
    VaultAPI.routes.extend(routes.get_all_routes())
    kwargs = dict(
        host=models.env.host,
        port=models.env.port,
        workers=models.env.workers,
        app=f"{module_name.parent.stem}.{module_name.stem}:{VaultAPI.title}",
    )
    if models.env.log_config:
        kwargs["log_config"] = models.env.log_config
    uvicorn.run(**kwargs)
