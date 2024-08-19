import requests
from cryptography.fernet import Fernet

from pyvault.models import session
from pyvault.squire import load_env

if __name__ == "__main__":
    env = load_env()
    session.fernet = Fernet(env.secret)
    base_url = f"http://{env.host}:{env.port}"
    health = f"{base_url}/health"
    assert requests.get(health).status_code == 200
    get_url = f"{base_url}/get-secret"
    response = requests.get(
        url=get_url,
        params={"filename": ".sample"},
        headers={"Authorization": f"Bearer {env.apikey}"},
    )
    encrypted = response.json().get("detail")
    print(session.fernet.decrypt(encrypted).decode())
