import logging

import uvicorn
from cryptography.fernet import Fernet
from fastapi import FastAPI

import vaultapi
from vaultapi import models, routers, squire

LOGGER = logging.getLogger("uvicorn.default")


def start(**kwargs) -> None:
    """Starter function for the API, which uses uvicorn server as trigger.

    Keyword Args:
        env_file: Env filepath to load the environment variables.
        apikey: API Key for authentication.
        ninja_host: Hostname for the API server.
        ninja_port: Port number for the API server.
        workers: Number of workers for the uvicorn server.
        remote_execution: Boolean flag to enable remote execution.
        api_secret: Secret access key for running commands on server remotely.
        database: FilePath to store the auth database that handles the authentication errors.
        rate_limit: List of dictionaries with ``max_requests`` and ``seconds`` to apply as rate limit.
        log_config: Logging configuration as a dict or a FilePath. Supports .yaml/.yml, .json or .ini formats.
    """
    models.env = squire.load_env(**kwargs)
    models.session.fernet = Fernet(models.env.secret)
    app = FastAPI(
        routes=routers.get_all_routes(),
        title="vaultapi",
        description="Lightweight service to serve secrets and environment variables",
        version=vaultapi.version,
    )
    kwargs = dict(
        host=models.env.host,
        port=models.env.port,
        workers=models.env.workers,
        app=app,
    )
    if models.env.log_config:
        kwargs["log_config"] = models.env.log_config
    uvicorn.run(**kwargs)
