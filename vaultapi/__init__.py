import sys

import click
from cryptography.fernet import Fernet

from .main import start, version


@click.command()
@click.argument("run", required=False)
@click.argument("start", required=False)
@click.argument("keygen", required=False)
@click.option("--version", "-V", is_flag=True, help="Prints the version.")
@click.option("--help", "-H", is_flag=True, help="Prints the help section.")
@click.option(
    "--env",
    "-E",
    type=click.Path(exists=True),
    help="Environment configuration filepath.",
)
def commandline(*args, **kwargs) -> None:
    """Starter function to invoke VaultAPI via CLI commands.

    **Flags**
        - ``--version | -V``: Prints the version.
        - ``--help | -H``: Prints the help section.
        - ``--env | -E``: Environment configuration filepath.
    """
    assert sys.argv[0].lower().endswith("vaultapi"), "Invalid commandline trigger!!"
    options = {
        "--version | -V": "Prints the version.",
        "--help | -H": "Prints the help section.",
        "--env | -E": "Environment configuration filepath.",
        "start | run": "Initiates the API server.",
    }
    # weird way to increase spacing to keep all values monotonic
    _longest_key = len(max(options.keys()))
    _pretext = "\n\t* "
    choices = _pretext + _pretext.join(
        f"{k} {'·' * (_longest_key - len(k) + 8)}→ {v}".expandtabs()
        for k, v in options.items()
    )
    if kwargs.get("version"):
        click.echo(f"VaultAPI {version.__version__}")
        sys.exit(0)
    if kwargs.get("help"):
        click.echo(
            f"\nUsage: vaultapi [arbitrary-command]\nOptions (and corresponding behavior):{choices}"
        )
        sys.exit(0)
    trigger = (
        kwargs.get("start") or kwargs.get("run") or kwargs.get("keygen") or ""
    ).lower()
    if trigger in ("start", "run"):
        start(env_file=kwargs.get("env"))
        sys.exit(0)
    elif trigger == "keygen":
        key = Fernet.generate_key()
        click.secho(
            f"\nStore this as an env var named 'secret' or pass it as kwargs\n\n{key.decode()}\n"
        )
        sys.exit(0)
    else:
        click.secho(f"\n{kwargs}\nNo command provided", fg="red")
    click.echo(
        f"Usage: vaultapi [arbitrary-command]\nOptions (and corresponding behavior):{choices}"
    )
    sys.exit(1)
