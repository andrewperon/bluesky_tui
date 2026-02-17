from __future__ import annotations

from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.widgets import Static, ListItem

from bluesky_tui.api.models import ConversationData


def _relative_time(sent_at: str) -> str:
    if not sent_at:
        return ""
    try:
        dt = datetime.fromisoformat(sent_at.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - dt
        seconds = int(delta.total_seconds())
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        if minutes < 60:
            return f"{minutes}m"
        hours = minutes // 60
        if hours < 24:
            return f"{hours}h"
        days = hours // 24
        if days < 30:
            return f"{days}d"
        return dt.strftime("%b %d")
    except Exception:
        return ""


class ConversationItem(ListItem):
    DEFAULT_CSS = """
    ConversationItem {
        height: auto;
        padding: 0 1;
        border-bottom: solid $surface-lighten-2;
    }
    ConversationItem.unread {
        background: $surface-lighten-1;
    }
    ConversationItem > .convo-header-line {
        text-style: bold;
    }
    ConversationItem > .convo-preview-line {
        color: $text-muted;
    }
    """

    def __init__(self, convo: ConversationData, my_did: str, **kwargs) -> None:
        super().__init__(**kwargs)
        self._convo = convo
        self._my_did = my_did

    def compose(self) -> ComposeResult:
        yield Static("", id="convo-header-line", classes="convo-header-line")
        yield Static("", id="convo-preview-line", classes="convo-preview-line")

    def on_mount(self) -> None:
        name = self._convo.display_name(self._my_did)
        ts = _relative_time(self._convo.last_message.sent_at) if self._convo.last_message else ""
        self.query_one("#convo-header-line", Static).update(
            f"[bold]{name}[/bold]  [dim]{ts}[/dim]"
        )
        preview = self._convo.last_message.text[:60] if self._convo.last_message else ""
        unread = (
            f"  [bold red]{self._convo.unread_count}[/bold red]"
            if self._convo.unread_count
            else ""
        )
        self.query_one("#convo-preview-line", Static).update(
            f"[dim]{preview}[/dim]{unread}"
        )
        if self._convo.unread_count:
            self.add_class("unread")

    @property
    def convo(self) -> ConversationData:
        return self._convo
