import pathlib
import re
import socket
import sqlite3
from typing import Any, Dict, List, Set, Tuple

from cryptography.fernet import Fernet
from pydantic import (
    BaseModel,
    Field,
    FilePath,
    HttpUrl,
    NewPath,
    PositiveInt,
    field_validator,
)
from pydantic_settings import BaseSettings


def complexity_checker(secret: str, simple: bool = False) -> None:
    """Verifies the strength of a secret.

    Args:
        secret: Value of the secret.
        simple: Boolean flag to increase complexity.

    See Also:
        A secret is considered strong if it at least has:

        - 32 characters
        - 1 digit
        - 1 symbol
        - 1 uppercase letter
        - 1 lowercase letter

    Raises:
        AssertionError: When at least 1 of the above conditions fail to match.
    """
    char_limit = 8 if simple else 32

    # calculates the length
    assert (
        len(secret) >= char_limit
    ), f"Minimum secret length is {char_limit}, received {len(secret)}"

    # searches for digits
    assert re.search(r"\d", secret), "secret must include an integer"

    if simple:
        return

    # searches for uppercase
    assert re.search(
        r"[A-Z]", secret
    ), "secret must include at least one uppercase letter"

    # searches for lowercase
    assert re.search(
        r"[a-z]", secret
    ), "secret must include at least one lowercase letter"

    # searches for symbols
    assert re.search(
        r"[ !#$%&'()*+,-./[\\\]^_`{|}~" + r'"]', secret
    ), "secret must contain at least one special character"


class Database:
    """Creates a connection and instantiates the cursor.

    >>> Database

    Args:
        filepath: Name of the database file.
        timeout: Timeout for the connection to database.
    """

    def __init__(self, filepath: FilePath | str, timeout: int = 10):
        """Instantiates the class ``Database`` to create a connection and a cursor."""
        if not filepath.endswith(".db"):
            filepath = filepath + ".db"
        self.connection = sqlite3.connect(
            database=filepath, check_same_thread=False, timeout=timeout
        )

    def create_table(self, table_name: str, columns: List[str] | Tuple[str]) -> None:
        """Creates the table with the required columns.

        Args:
            table_name: Name of the table that has to be created.
            columns: List of columns that has to be created.
        """
        with self.connection:
            cursor = self.connection.cursor()
            # Use f-string or %s as table names cannot be parametrized
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {table_name!r} ({', '.join(columns)})"
            )


database: Database = Database  # noqa: PyTypeChecker


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

    fernet: Fernet | None = None
    info: Dict[str, str] = {}
    rps: Dict[str, int] = {}
    allowed_origins: Set[str] = set()

    class Config:
        """Config to allow arbitrary types."""

        arbitrary_types_allowed = True


class EnvConfig(BaseSettings):
    """Object to load environment variables.

    >>> EnvConfig

    """

    apikey: str
    secret: str
    database: FilePath | NewPath | str = Field("secrets.db", pattern=".*.db$")
    endpoints: HttpUrl | List[HttpUrl] = []
    host: str = socket.gethostbyname("localhost") or "0.0.0.0"
    port: PositiveInt = 8080
    workers: PositiveInt = 1
    log_config: FilePath | Dict[str, Any] | None = None
    allowed_origins: List[str] = []
    rate_limit: RateLimit | List[RateLimit] = []

    @field_validator("endpoints", mode="after", check_fields=True)
    def parse_endpoints(
        cls, value: HttpUrl | List[HttpUrl]
    ) -> List[HttpUrl]:  # noqa: PyMethodParameters
        """Validate endpoints to enable CORS policy."""
        if isinstance(value, list):
            return value
        return [value]

    @field_validator("apikey", mode="after")
    def parse_apikey(cls, value: str | None) -> str | None:  # noqa: PyMethodParameters
        """Parse API key to validate complexity."""
        if value:
            try:
                complexity_checker(value, True)
            except AssertionError as error:
                raise ValueError(error.__str__())
            return value

    @field_validator("secret", mode="after")
    def parse_api_secret(
        cls, value: str | None
    ) -> str | None:  # noqa: PyMethodParameters
        """Parse API secret to validate complexity."""
        if value:
            try:
                complexity_checker(value)
            except AssertionError as error:
                raise ValueError(error.__str__())
            return value

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


# noinspection PyTypeChecker
env: EnvConfig = EnvConfig
session = Session()
