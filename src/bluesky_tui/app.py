from pathlib import Path

from textual.app import App

from bluesky_tui.api.client import BlueskyClient


class BlueskyApp(App):
    TITLE = "Bluesky TUI"
    CSS_PATH = "css/app.tcss"

    def __init__(self) -> None:
        super().__init__()
        self.client = BlueskyClient()

    async def on_mount(self) -> None:
        from bluesky_tui.config import load_credentials

        creds = load_credentials()
        if creds:
            try:
                await self.client.login(creds["handle"], creds["app_password"])
                from bluesky_tui.screens.feed import FeedScreen
                self.push_screen(FeedScreen())
                return
            except Exception:
                pass

        from bluesky_tui.screens.login import LoginScreen
        self.push_screen(LoginScreen())
