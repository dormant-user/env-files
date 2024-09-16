import logging
import pathlib

import uvicorn
from cryptography.fernet import Fernet
from fastapi import FastAPI

from . import models, routers, squire, version

LOGGER = logging.getLogger("uvicorn.default")
VaultAPI = FastAPI(
    title="VaultAPI",
    description="Lightweight service to serve secrets and environment variables",
    version=version.__version__,
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
    models.env = squire.load_env(**kwargs)
    models.session.fernet = Fernet(models.env.secret)
    models.database = models.Database(models.env.database)
    models.database.create_table("default", ["key", "value"])
    module_name = pathlib.Path(__file__)
    VaultAPI.routes.extend(routers.get_all_routes())
    kwargs = dict(
        host=models.env.host,
        port=models.env.port,
        workers=models.env.workers,
        app=f"{module_name.parent.stem}.{module_name.stem}:{VaultAPI.title}",
    )
    if models.env.log_config:
        kwargs["log_config"] = models.env.log_config
    uvicorn.run(**kwargs)
