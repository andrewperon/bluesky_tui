from __future__ import annotations

from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.widgets import Static, ListItem

from bluesky_tui.api.models import NotificationData

REASON_ICONS = {
    "like": "[red]❤[/red]",
    "repost": "[green]↻[/green]",
    "follow": "[blue]👤[/blue]",
    "mention": "[yellow]@[/yellow]",
    "reply": "[cyan]💬[/cyan]",
    "quote": "[magenta]❝[/magenta]",
    "like-via-repost": "[red]❤[/red][green]↻[/green]",
}

REASON_VERBS = {
    "like": "liked your post",
    "repost": "reposted your post",
    "follow": "followed you",
    "mention": "mentioned you",
    "reply": "replied to you",
    "quote": "quoted your post",
    "like-via-repost": "liked your repost",
}


def _relative_time(created_at: str) -> str:
    if not created_at:
        return ""
    try:
        dt = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
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


class NotificationItem(ListItem):
    DEFAULT_CSS = """
    NotificationItem {
        height: auto;
        padding: 0 1;
        border-bottom: solid $surface-lighten-2;
    }
    NotificationItem.unread {
        background: $surface-lighten-1;
    }
    NotificationItem > .notif-header {
        /* icon + author + verb + timestamp all on one line */
    }
    NotificationItem > .notif-text {
        padding: 0 0 0 4;
        color: $text;
    }
    """

    def __init__(self, data: NotificationData, **kwargs) -> None:
        super().__init__(**kwargs)
        self.data = data

    def compose(self) -> ComposeResult:
        d = self.data
        icon = REASON_ICONS.get(d.reason, "?")
        verb = REASON_VERBS.get(d.reason, d.reason)
        ts = _relative_time(d.created_at)

        header = (
            f"{icon} [bold]{d.author_display_name}[/bold] "
            f"[dim]@{d.author_handle}[/dim] "
            f"{verb}"
            f"  [dim]{ts}[/dim]"
        )
        yield Static(header, classes="notif-header")

        if d.text:
            yield Static(d.text[:200], classes="notif-text")

    def on_mount(self) -> None:
        if not self.data.is_read:
            self.add_class("unread")


class GroupedNotificationItem(ListItem):
    """A notification item representing multiple users for the same action on the same post."""

    DEFAULT_CSS = """
    GroupedNotificationItem {
        height: auto;
        padding: 0 1;
        border-bottom: solid $surface-lighten-2;
    }
    GroupedNotificationItem.unread {
        background: $surface-lighten-1;
    }
    GroupedNotificationItem > .notif-header {
    }
    GroupedNotificationItem > .notif-text {
        padding: 0 0 0 4;
        color: $text;
    }
    """

    def __init__(self, notifications: list[NotificationData], **kwargs) -> None:
        super().__init__(**kwargs)
        self.notifications = notifications
        self.data = notifications[0]  # primary notification for navigation

    def compose(self) -> ComposeResult:
        d = self.data
        icon = REASON_ICONS.get(d.reason, "?")
        verb = REASON_VERBS.get(d.reason, d.reason)
        ts = _relative_time(d.created_at)

        names = [n.author_display_name for n in self.notifications]
        if len(names) == 1:
            who = f"[bold]{names[0]}[/bold]"
        elif len(names) == 2:
            who = f"[bold]{names[0]}[/bold] and [bold]{names[1]}[/bold]"
        else:
            who = f"[bold]{names[0]}[/bold], [bold]{names[1]}[/bold] and {len(names) - 2} others"

        header = f"{icon} {who} {verb}  [dim]{ts}[/dim]"
        yield Static(header, classes="notif-header")

        if d.text:
            yield Static(d.text[:200], classes="notif-text")

    def on_mount(self) -> None:
        if any(not n.is_read for n in self.notifications):
            self.add_class("unread")
