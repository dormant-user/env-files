from typing import List, Tuple

from . import models


def get_secret(key: str, table_name: str) -> str | None:
    """Function to retrieve secret from database.

    Args:
        key: Name of the secret to retrieve.
        table_name: Name of the table where the secret is stored.

    Returns:
        str:
        Returns the secret value.
    """
    with models.database.connection:
        cursor = models.database.connection.cursor()
        state = cursor.execute(
            f'SELECT value FROM "{table_name}" WHERE key=(?)', (key,)
        ).fetchone()
    if state and state[0]:
        return state[0]


def get_table(table_name: str) -> List[Tuple[str, str]]:
    """Function to retrieve all key-value pairs from a particular table in the database.

    Args:
        table_name: Name of the table where the secrets are stored.

    Returns:
        str:
        Returns the secret value.
    """
    with models.database.connection:
        cursor = models.database.connection.cursor()
        state = cursor.execute(f'SELECT * FROM "{table_name}"').fetchall()
    return state


def put_secret(key: str, value: str, table_name: str) -> None:
    """Function to add secret to the database.

    Args:
        key: Name of the secret to be stored.
        value: Value of the secret to be stored
        table_name: Name of the table where the secret is stored.
    """
    with models.database.connection:
        cursor = models.database.connection.cursor()
        cursor.execute(
            f'INSERT INTO "{table_name}" (key, value) VALUES (?,?)',
            (key, value),
        )
        models.database.connection.commit()


def remove_secret(key: str, table_name: str) -> None:
    """Function to remove a secret from the database.

    Args:
        key: Name of the secret to be removed.
        table_name: Name of the table where the secret is stored.
    """
    with models.database.connection:
        cursor = models.database.connection.cursor()
        cursor.execute(f'DELETE FROM "{table_name}" WHERE key=(?)', (key,))
        models.database.connection.commit()
