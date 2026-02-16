from __future__ import annotations

from datetime import datetime, timezone

from textual.app import ComposeResult
from textual.widgets import Static, ListItem
from textual.reactive import reactive

from bluesky_tui.api.models import PostData


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


class PostWidget(ListItem):
    COMPONENT_CLASSES = {"post--highlighted"}

    DEFAULT_CSS = """
    PostWidget {
        height: auto;
        padding: 0 1;
        border-bottom: solid $surface-lighten-2;
    }
    PostWidget.--highlight {
        background: $surface-lighten-1;
    }
    PostWidget > .post-repost-line {
        color: $text-muted;
        text-style: italic;
    }
    PostWidget > .post-reply-line {
        color: $text-muted;
        text-style: italic;
    }
    PostWidget > .post-text {
        padding: 0 0 0 2;
    }
    PostWidget > .post-stats {
        color: $text-muted;
        padding: 0 0 0 2;
    }
    """

    post_data: reactive[PostData | None] = reactive(None)

    def __init__(self, post_data: PostData, **kwargs) -> None:
        super().__init__(**kwargs)
        self.post_data = post_data

    def compose(self) -> ComposeResult:
        yield Static("", id="repost-line", classes="post-repost-line")
        yield Static("", id="reply-line", classes="post-reply-line")
        yield Static("", id="author-line")
        yield Static("", id="text-line", classes="post-text")
        yield Static("", id="stats-line", classes="post-stats")

    def on_mount(self) -> None:
        self._refresh_display()

    def watch_post_data(self) -> None:
        if self.is_mounted:
            self._refresh_display()

    def _refresh_display(self) -> None:
        data = self.post_data
        if not data:
            return

        repost_line = self.query_one("#repost-line", Static)
        if data.reason_repost_by:
            repost_line.update(f"  ↻ Reposted by @{data.reason_repost_by}")
            repost_line.display = True
        else:
            repost_line.display = False

        reply_line = self.query_one("#reply-line", Static)
        if data.reply_parent_author:
            reply_line.update(f"  ↩ Reply to @{data.reply_parent_author}")
            reply_line.display = True
        else:
            reply_line.display = False

        author_line = self.query_one("#author-line", Static)
        timestamp = _relative_time(data.created_at)
        author_line.update(
            f"[bold]{data.author_display_name}[/bold] [dim]@{data.author_handle}[/dim]"
            f"  [dim]{timestamp}[/dim]"
        )

        text_line = self.query_one("#text-line", Static)
        text = data.text
        if data.has_image:
            text += " [blue]📷[/blue]"
        if data.has_video:
            text += " [blue]🎬[/blue]"
        text_line.update(text)

        like_indicator = "❤" if data.is_liked else "♡"
        repost_indicator = "↻✓" if data.is_reposted else "↻"
        stats = (
            f"{like_indicator} {data.like_count}  "
            f"{repost_indicator} {data.repost_count}  "
            f"💬 {data.reply_count}"
        )
        self.query_one("#stats-line", Static).update(stats)
