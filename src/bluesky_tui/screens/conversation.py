from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, Input, Button
from textual.containers import Horizontal

from bluesky_tui.widgets.message_item import MessageItem
from bluesky_tui.api.models import ConversationData, MessageData


class ConversationScreen(Screen):
    BINDINGS = [
        Binding("i", "focus_input", "Compose", show=True),
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self, convo: ConversationData) -> None:
        super().__init__()
        self._convo = convo
        self._last_message_id: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("", id="convo-title")
        yield ListView(id="message-list")
        yield Horizontal(
            Input(placeholder="Type a message...", id="message-input"),
            Button("Send", id="send-button", variant="primary"),
            id="message-compose-bar",
        )
        yield Footer()

    def on_mount(self) -> None:
        my_did = self.app.client.me.did if self.app.client.me else ""
        name = self._convo.display_name(my_did)
        self.query_one("#convo-title", Static).update(f"Conversation with {name}")
        self._load_messages()
        self.set_interval(60, self._poll_new_messages)

    @work
    async def _load_messages(self) -> None:
        status = self.query_one("#convo-title", Static)
        try:
            messages, _ = await self.app.client.get_messages(self._convo.id)
            message_list = self.query_one("#message-list", ListView)
            message_list.clear()
            for msg in messages:
                message_list.append(MessageItem(msg))
            if messages:
                self._last_message_id = messages[-1].id
                # Mark as read
                try:
                    await self.app.client.mark_convo_read(self._convo.id, messages[-1].id)
                except Exception:
                    pass
            # Scroll to bottom so newest messages are visible
            message_list.scroll_end(animate=False)
        except Exception as e:
            err = str(e).lower()
            if "unauthorized" in err or "forbidden" in err or "401" in err or "403" in err:
                self.app.notify(
                    "DM access requires an app password with messaging permissions enabled. "
                    "Please re-login with a new app password.",
                    severity="error",
                    timeout=8,
                )
            else:
                self.app.notify(f"Failed to load messages: {e}", severity="error")

    def _poll_new_messages(self) -> None:
        self._fetch_new_messages()

    @work
    async def _fetch_new_messages(self) -> None:
        try:
            messages, _ = await self.app.client.get_messages(self._convo.id)
            if not messages:
                return
            # Find messages newer than last known
            if self._last_message_id is None:
                new_messages = messages
            else:
                found = False
                new_messages = []
                for msg in messages:
                    if found:
                        new_messages.append(msg)
                    elif msg.id == self._last_message_id:
                        found = True
                if not found:
                    # Last known message not in response — replace all
                    new_messages = messages
            if new_messages:
                message_list = self.query_one("#message-list", ListView)
                for msg in new_messages:
                    message_list.append(MessageItem(msg))
                self._last_message_id = new_messages[-1].id
                message_list.scroll_end(animate=False)
                try:
                    await self.app.client.mark_convo_read(self._convo.id, self._last_message_id)
                except Exception:
                    pass
        except Exception:
            pass  # Silent poll failures — don't spam notifications

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "message-input":
            self._send_message(event.value)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "send-button":
            input_widget = self.query_one("#message-input", Input)
            self._send_message(input_widget.value)

    def _send_message(self, text: str) -> None:
        text = text.strip()
        if not text:
            return
        input_widget = self.query_one("#message-input", Input)
        input_widget.value = ""
        self._do_send(text)

    @work
    async def _do_send(self, text: str) -> None:
        # Optimistic: append a placeholder message immediately
        my_did = self.app.client.me.did if self.app.client.me else ""
        from datetime import datetime, timezone
        optimistic = MessageData(
            id="__optimistic__",
            convo_id=self._convo.id,
            sender_did=my_did,
            sender_handle=self.app.client.me.handle if self.app.client.me else "",
            sender_display_name=self.app.client.me.display_name if self.app.client.me else "",
            text=text,
            sent_at=datetime.now(timezone.utc).isoformat(),
            is_mine=True,
        )
        message_list = self.query_one("#message-list", ListView)
        optimistic_widget = MessageItem(optimistic)
        message_list.append(optimistic_widget)
        message_list.scroll_end(animate=False)

        try:
            real_msg = await self.app.client.send_dm(self._convo.id, text)
            self._last_message_id = real_msg.id
            # Replace optimistic widget with real one
            optimistic_widget.remove()
            message_list.append(MessageItem(real_msg))
            message_list.scroll_end(animate=False)
        except Exception as e:
            optimistic_widget.remove()
            self.app.notify(f"Failed to send message: {e}", severity="error")

    def action_focus_input(self) -> None:
        self.query_one("#message-input", Input).focus()

    def action_go_back(self) -> None:
        self.app.pop_screen()
