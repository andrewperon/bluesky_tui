from __future__ import annotations

from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.widgets import Static, ListItem

from bluesky_tui.api.models import MessageData


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


class MessageItem(ListItem):
    DEFAULT_CSS = """
    MessageItem {
        height: auto;
        padding: 0 1;
    }
    MessageItem.sent {
        background: $surface-lighten-1;
        border-left: thick $accent;
    }
    MessageItem.received {
        border-left: thick $surface-lighten-3;
    }
    MessageItem > .msg-header {
        color: $text-muted;
    }
    MessageItem > .msg-text {
        padding: 0 0 0 2;
    }
    """

    def __init__(self, message: MessageData, **kwargs) -> None:
        super().__init__(**kwargs)
        self._message = message

    def compose(self) -> ComposeResult:
        yield Static("", id="msg-header", classes="msg-header")
        yield Static("", id="msg-text", classes="msg-text")

    def on_mount(self) -> None:
        m = self._message
        ts = _relative_time(m.sent_at)
        if m.is_mine:
            self.add_class("sent")
            self.query_one("#msg-header", Static).update(
                f"[dim]{ts}[/dim]  [bold]You[/bold]"
            )
        else:
            self.add_class("received")
            name = m.sender_display_name or m.sender_handle
            self.query_one("#msg-header", Static).update(
                f"[bold]{name}[/bold]  [dim]{ts}[/dim]"
            )
        self.query_one("#msg-text", Static).update(m.text)

    @property
    def message(self) -> MessageData:
        return self._message
