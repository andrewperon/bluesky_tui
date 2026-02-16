from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea, Button
from textual.containers import Vertical, Horizontal

from bluesky_tui.api.models import PostData

MAX_CHARS = 300


class ComposeScreen(ModalScreen[PostData | None]):
    CSS = """
    ComposeScreen {
        align: center middle;
    }
    #compose-box {
        width: 70;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        border: thick $accent;
        background: $surface;
    }
    #compose-title {
        text-style: bold;
        margin-bottom: 1;
    }
    #compose-context {
        color: $text-muted;
        margin-bottom: 1;
        display: none;
    }
    #compose-context.visible {
        display: block;
    }
    #char-count {
        text-align: right;
        color: $text-muted;
    }
    #char-count.over-limit {
        color: $error;
        text-style: bold;
    }
    #compose-buttons {
        margin-top: 1;
        height: 3;
    }
    #compose-buttons Button {
        margin: 0 1;
    }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]

    def __init__(
        self,
        reply_to: PostData | None = None,
        quote: PostData | None = None,
    ) -> None:
        super().__init__()
        self._reply_to = reply_to
        self._quote = quote

    def compose(self) -> ComposeResult:
        with Vertical(id="compose-box"):
            if self._reply_to:
                title = "Reply"
            elif self._quote:
                title = "Quote Post"
            else:
                title = "New Post"
            yield Static(title, id="compose-title")
            context = Static("", id="compose-context")
            yield context
            yield TextArea(id="compose-text")
            yield Static(f"0 / {MAX_CHARS}", id="char-count")
            with Horizontal(id="compose-buttons"):
                yield Button("Post", variant="primary", id="post-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")

    def on_mount(self) -> None:
        context = self.query_one("#compose-context", Static)
        if self._reply_to:
            context.update(
                f"Replying to @{self._reply_to.author_handle}:\n"
                f"{self._reply_to.text[:100]}{'...' if len(self._reply_to.text) > 100 else ''}"
            )
            context.add_class("visible")
        elif self._quote:
            context.update(
                f"Quoting @{self._quote.author_handle}:\n"
                f"{self._quote.text[:100]}{'...' if len(self._quote.text) > 100 else ''}"
            )
            context.add_class("visible")
        self.query_one("#compose-text", TextArea).focus()

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        text = event.text_area.text
        count = len(text)
        counter = self.query_one("#char-count", Static)
        counter.update(f"{count} / {MAX_CHARS}")
        if count > MAX_CHARS:
            counter.add_class("over-limit")
        else:
            counter.remove_class("over-limit")
        self.query_one("#post-btn", Button).disabled = count == 0 or count > MAX_CHARS

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "post-btn":
            self._send_post()
        elif event.button.id == "cancel-btn":
            self.dismiss(None)

    def action_cancel(self) -> None:
        self.dismiss(None)

    @work
    async def _send_post(self) -> None:
        text = self.query_one("#compose-text", TextArea).text.strip()
        if not text:
            return
        btn = self.query_one("#post-btn", Button)
        btn.disabled = True
        btn.label = "Posting..."
        try:
            post = await self.app.client.create_post(
                text=text,
                reply_to=self._reply_to,
                quote=self._quote,
            )
            self.app.notify("Post sent!")
            self.dismiss(post)
        except Exception as e:
            self.app.notify(f"Failed to post: {e}", severity="error")
            btn.disabled = False
            btn.label = "Post"
