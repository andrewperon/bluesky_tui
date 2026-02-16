from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import Static
from textual.containers import Vertical

from bluesky_tui.api.models import ProfileData


class UserHeader(Static):
    CSS = """
    UserHeader {
        height: auto;
        padding: 1 2;
        border-bottom: solid $accent;
        background: $surface-lighten-1;
    }
    .profile-name {
        text-style: bold;
        margin-bottom: 0;
    }
    .profile-handle {
        color: $text-muted;
    }
    .profile-bio {
        margin: 1 0;
    }
    .profile-stats {
        color: $text-muted;
    }
    .profile-following-status {
        color: $success;
        text-style: italic;
    }
    """

    def __init__(self, profile: ProfileData, **kwargs) -> None:
        super().__init__(**kwargs)
        self._profile = profile

    def compose(self) -> ComposeResult:
        p = self._profile
        yield Static(p.display_name, classes="profile-name")
        yield Static(f"@{p.handle}", classes="profile-handle")
        if p.description:
            yield Static(p.description, classes="profile-bio")
        yield Static(
            f"{p.followers_count} followers  {p.following_count} following  {p.posts_count} posts",
            classes="profile-stats",
        )
        if p.is_following:
            yield Static("Following", classes="profile-following-status")

    def update_profile(self, profile: ProfileData) -> None:
        self._profile = profile
        self.remove_children()
        self.mount_all(list(self.compose()))
