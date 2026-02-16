import json
import logging
from pathlib import Path

import keyring

SERVICE_NAME = "bluesky_tui"
CONFIG_DIR = Path.home() / ".config" / "bluesky_tui"
CONFIG_FILE = CONFIG_DIR / "config.json"

log = logging.getLogger(__name__)


def load_credentials() -> dict | None:
    """Load credentials from system keyring, falling back to legacy config file."""
    # Try keyring first
    try:
        blob = keyring.get_password(SERVICE_NAME, "credentials")
        if blob:
            data = json.loads(blob)
            if data.get("handle") and data.get("app_password"):
                return data
    except Exception as e:
        log.debug("Keyring read failed: %s", e)

    # Fall back to legacy plaintext config
    if CONFIG_FILE.exists():
        try:
            data = json.loads(CONFIG_FILE.read_text())
            if data.get("handle") and data.get("app_password"):
                # Migrate to keyring
                _save_to_keyring(data["handle"], data["app_password"])
                _remove_legacy_config()
                return data
        except (json.JSONDecodeError, KeyError):
            pass

    return None


def save_credentials(handle: str, app_password: str) -> None:
    """Save credentials to system keyring."""
    _save_to_keyring(handle, app_password)
    # Remove legacy plaintext file if it exists
    _remove_legacy_config()


def clear_credentials() -> None:
    """Remove credentials from keyring and any legacy config file."""
    try:
        keyring.delete_password(SERVICE_NAME, "credentials")
    except Exception as e:
        log.debug("Keyring delete failed: %s", e)
    _remove_legacy_config()


def _save_to_keyring(handle: str, app_password: str) -> None:
    blob = json.dumps({"handle": handle, "app_password": app_password})
    try:
        keyring.set_password(SERVICE_NAME, "credentials", blob)
    except Exception as e:
        log.warning("Keyring write failed, falling back to config file: %s", e)
        _save_to_file(handle, app_password)


def _save_to_file(handle: str, app_password: str) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps({
        "handle": handle,
        "app_password": app_password,
    }))
    CONFIG_FILE.chmod(0o600)


def _remove_legacy_config() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
