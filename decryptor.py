import requests
from cryptography.fernet import Fernet

from vaultapi.models import session
from vaultapi.squire import load_env

env = load_env()
session.fernet = Fernet(env.secret)

BASE_URL = f"http://{env.host}:{env.port}"
assert requests.get(f"{BASE_URL}/health").status_code == 200


def get_secret(filename: str, filepath: str):
    """Get secret file contents from the API.

    Args:
        filename: Filename to source secrets.
        filepath: Parent directory path for the secrets file.
    """
    get_url = f"{BASE_URL}/get-secret"
    response = requests.get(
        url=get_url,
        params={"filename": filename, "filepath": filepath},
        headers={"Authorization": f"Bearer {env.apikey}"},
    )
    encrypted = response.json().get("detail")
    print(session.fernet.decrypt(encrypted).decode())
