import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".config" / "bluesky_tui"
CONFIG_FILE = CONFIG_DIR / "config.json"


def load_credentials() -> dict | None:
    if not CONFIG_FILE.exists():
        return None
    try:
        data = json.loads(CONFIG_FILE.read_text())
        if data.get("handle") and data.get("app_password"):
            return data
    except (json.JSONDecodeError, KeyError):
        pass
    return None


def save_credentials(handle: str, app_password: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({
        "handle": handle,
        "app_password": app_password,
    }))
    CONFIG_FILE.chmod(0o600)


def clear_credentials() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
