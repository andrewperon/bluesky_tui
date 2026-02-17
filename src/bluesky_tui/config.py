import json
import logging
from pathlib import Path

import keyring

SERVICE_NAME = "bluesky_tui"
CONFIG_DIR = Path.home() / ".config" / "bluesky_tui"
CONFIG_FILE = CONFIG_DIR / "config.json"

log = logging.getLogger(__name__)

DEFAULT_SETTINGS: dict = {
    "theme": "textual-dark",
    "post_density": "normal",
    "default_filter": "all",
    "posts_per_page": 30,
    "notification_filters": {
        "like": True,
        "repost": True,
        "reply": True,
        "follow": True,
        "mention": True,
        "quote": True,
    },
}


def load_settings() -> dict:
    """Load settings from keyring, returning defaults for any missing keys."""
    settings = dict(DEFAULT_SETTINGS)
    try:
        blob = keyring.get_password(SERVICE_NAME, "settings")
        if blob:
            stored = json.loads(blob)
            for key, value in stored.items():
                if key == "notification_filters" and isinstance(value, dict):
                    settings["notification_filters"] = {
                        **DEFAULT_SETTINGS["notification_filters"],
                        **value,
                    }
                else:
                    settings[key] = value
    except Exception as e:
        log.debug("Failed to load settings: %s", e)
    return settings


def save_settings(settings: dict) -> None:
    """Save settings to keyring."""
    try:
        keyring.set_password(SERVICE_NAME, "settings", json.dumps(settings))
    except Exception as e:
        log.warning("Failed to save settings: %s", e)


# ---------------------------------------------------------------------------
# Multi-account storage
# ---------------------------------------------------------------------------

def load_accounts() -> dict:
    """Load the multi-account blob from keyring.

    Migrates from the old single-account ``"credentials"`` key and legacy
    config file if needed.

    Returns a dict with ``"active"`` (str | None) and ``"accounts"`` (list).
    """
    # Try new "accounts" key first
    try:
        blob = keyring.get_password(SERVICE_NAME, "accounts")
        if blob:
            data = json.loads(blob)
            if "accounts" in data:
                return data
    except Exception as e:
        log.debug("Keyring read (accounts) failed: %s", e)

    # Migrate from old "credentials" key
    try:
        blob = keyring.get_password(SERVICE_NAME, "credentials")
        if blob:
            old = json.loads(blob)
            if old.get("handle") and old.get("app_password"):
                new_data = {
                    "active": old["handle"],
                    "accounts": [
                        {"handle": old["handle"], "app_password": old["app_password"]}
                    ],
                }
                save_accounts(new_data)
                try:
                    keyring.delete_password(SERVICE_NAME, "credentials")
                except Exception:
                    pass
                return new_data
    except Exception as e:
        log.debug("Keyring read (credentials) failed: %s", e)

    # Migrate from legacy plaintext config file
    if CONFIG_FILE.exists():
        try:
            old = json.loads(CONFIG_FILE.read_text())
            if old.get("handle") and old.get("app_password"):
                new_data = {
                    "active": old["handle"],
                    "accounts": [
                        {"handle": old["handle"], "app_password": old["app_password"]}
                    ],
                }
                save_accounts(new_data)
                _remove_legacy_config()
                return new_data
        except (json.JSONDecodeError, KeyError):
            pass

    return {"active": None, "accounts": []}


def save_accounts(data: dict) -> None:
    """Save the multi-account blob to keyring."""
    try:
        keyring.set_password(SERVICE_NAME, "accounts", json.dumps(data))
    except Exception as e:
        log.warning("Keyring write (accounts) failed: %s", e)


def get_active_credentials() -> dict | None:
    """Return ``{"handle", "app_password"}`` for the active account, or None."""
    data = load_accounts()
    active = data.get("active")
    if not active:
        return None
    for acct in data.get("accounts", []):
        if acct["handle"] == active:
            return {"handle": acct["handle"], "app_password": acct["app_password"]}
    return None


def add_account(handle: str, app_password: str) -> None:
    """Add or update an account and set it as active."""
    data = load_accounts()
    # Update existing or append
    found = False
    for acct in data["accounts"]:
        if acct["handle"] == handle:
            acct["app_password"] = app_password
            found = True
            break
    if not found:
        data["accounts"].append({"handle": handle, "app_password": app_password})
    data["active"] = handle
    save_accounts(data)


def remove_account(handle: str) -> None:
    """Remove an account. If it was active, set the next one (or clear)."""
    data = load_accounts()
    data["accounts"] = [a for a in data["accounts"] if a["handle"] != handle]
    if data.get("active") == handle:
        data["active"] = data["accounts"][0]["handle"] if data["accounts"] else None
    save_accounts(data)


def set_active_account(handle: str) -> None:
    """Set which account is active."""
    data = load_accounts()
    data["active"] = handle
    save_accounts(data)


# ---------------------------------------------------------------------------
# Backward-compatible wrappers
# ---------------------------------------------------------------------------

def load_credentials() -> dict | None:
    """Load credentials for the active account.

    Thin wrapper around :func:`get_active_credentials` so that the existing
    app startup code continues to work unchanged.
    """
    return get_active_credentials()


def save_credentials(handle: str, app_password: str) -> None:
    """Save credentials (adds/updates account and sets it active)."""
    add_account(handle, app_password)


def clear_credentials() -> None:
    """Remove the active account and delete legacy artefacts."""
    data = load_accounts()
    active = data.get("active")
    if active:
        remove_account(active)
    _remove_legacy_config()


def _remove_legacy_config() -> None:
    if CONFIG_FILE.exists():
        CONFIG_FILE.unlink()
