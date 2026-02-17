from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView

from bluesky_tui.widgets.conversation_item import ConversationItem
from bluesky_tui.api.models import ConversationData


class ConversationsScreen(Screen):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "open_conversation", "Open"),
        Binding("R", "refresh", "Refresh"),
        Binding("space", "load_more", "More", show=False),
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._cursor: str | None = None
        self._all_convos: list[ConversationData] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Messages", id="conversations-title")
        yield ListView(id="convo-list")
        yield Static("Loading...", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._load_conversations()
        self.set_interval(60, self._load_conversations)

    @work
    async def _load_conversations(self) -> None:
        status = self.query_one("#status-bar", Static)
        status.update("Loading messages...")
        try:
            convos, cursor = await self.app.client.list_conversations()
            self._cursor = cursor
            self._all_convos = list(convos)
            self._rebuild_list()
            self._update_title()
            status.update("")
        except Exception as e:
            msg = str(e).lower()
            if "unauthorized" in msg or "forbidden" in msg or "401" in msg or "403" in msg:
                status.update("DM access unavailable")
                self.app.notify(
                    "DM access requires an app password with messaging permissions enabled. "
                    "Please re-login with a new app password.",
                    severity="error",
                    timeout=8,
                )
            else:
                status.update(f"Error: {e}")
                self.app.notify(f"Failed to load messages: {e}", severity="error")

    def _rebuild_list(self) -> None:
        convo_list = self.query_one("#convo-list", ListView)
        convo_list.clear()
        my_did = self.app.client.me.did if self.app.client.me else ""
        for convo in self._all_convos:
            convo_list.append(ConversationItem(convo, my_did))

    def _update_title(self) -> None:
        total_unread = sum(c.unread_count for c in self._all_convos)
        title = self.query_one("#conversations-title", Static)
        if total_unread:
            title.update(f"Messages  [bold red]({total_unread} unread)[/bold red]")
        else:
            title.update("Messages")

    def action_cursor_down(self) -> None:
        self.query_one("#convo-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#convo-list", ListView).action_cursor_up()

    def action_open_conversation(self) -> None:
        convo_list = self.query_one("#convo-list", ListView)
        item = convo_list.highlighted_child
        if isinstance(item, ConversationItem):
            from bluesky_tui.screens.conversation import ConversationScreen
            self.app.push_screen(ConversationScreen(item.convo))

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, ConversationItem):
            from bluesky_tui.screens.conversation import ConversationScreen
            self.app.push_screen(ConversationScreen(event.item.convo))

    def action_refresh(self) -> None:
        self._cursor = None
        self._all_convos = []
        self._load_conversations()

    @work
    async def _load_more(self) -> None:
        if not self._cursor:
            return
        status = self.query_one("#status-bar", Static)
        status.update("Loading more...")
        try:
            convos, cursor = await self.app.client.list_conversations(cursor=self._cursor)
            self._cursor = cursor
            self._all_convos.extend(convos)
            my_did = self.app.client.me.did if self.app.client.me else ""
            convo_list = self.query_one("#convo-list", ListView)
            for convo in convos:
                convo_list.append(ConversationItem(convo, my_did))
            self._update_title()
            status.update("")
        except Exception as e:
            self.app.notify(f"Failed to load more: {e}", severity="error")
            status.update("")

    def action_load_more(self) -> None:
        self._load_more()

    def action_go_back(self) -> None:
        self.app.pop_screen()
