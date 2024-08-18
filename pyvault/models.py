import pathlib
import socket
from typing import Any, Dict, List, Set

from pydantic import BaseModel, FilePath, PositiveInt
from pydantic_settings import BaseSettings


class RateLimit(BaseModel):
    """Object to store the rate limit settings.

    >>> RateLimit

    """

    max_requests: PositiveInt
    seconds: PositiveInt


class Session(BaseModel):
    """Object to store session information.

    >>> Session

    """

    info: Dict[str, str] = {}
    rps: Dict[str, int] = {}
    allowed_origins: Set[str] = set()


class EnvConfig(BaseSettings):
    """Object to load environment variables.

    >>> EnvConfig

    """

    apikey: str
    host: str = socket.gethostbyname("localhost") or "0.0.0.0"
    port: PositiveInt = 8080
    workers: PositiveInt = 1
    log_config: FilePath | Dict[str, Any] | None = None
    allowed_origins: List[str] = []
    rate_limit: RateLimit | List[RateLimit] = []

    @classmethod
    def from_env_file(cls, env_file: pathlib.Path) -> "EnvConfig":
        """Create Settings instance from environment file.

        Args:
            env_file: Name of the env file.

        Returns:
            EnvConfig:
            Loads the ``EnvConfig`` model.
        """
        return cls(_env_file=env_file)

    class Config:
        """Extra configuration for EnvConfig object."""

        extra = "ignore"
        hide_input_in_errors = True
        arbitrary_types_allowed = True


env = EnvConfig
session = Session()
