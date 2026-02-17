from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem


class AccountItem(ListItem):
    """A row representing a saved account."""

    def __init__(self, handle: str, is_active: bool) -> None:
        super().__init__()
        self.handle = handle
        self.is_active = is_active

    def compose(self) -> ComposeResult:
        marker = " *" if self.is_active else ""
        yield Static(f"  @{self.handle}{marker}", classes="account-text")


class AddAccountItem(ListItem):
    """A row for adding a new account."""

    def compose(self) -> ComposeResult:
        yield Static("  + Add account", classes="account-text")


class AccountSwitcherScreen(Screen):
    CSS = """
    AccountSwitcherScreen ListView {
        background: $background;
    }
    AccountSwitcherScreen ListView > ListItem {
        padding: 0;
        height: 1;
        background: $background;
    }
    AccountSwitcherScreen ListView > ListItem.--highlight {
        background: $accent;
    }
    .account-text {
        padding: 0 1;
    }
    #switcher-title {
        text-style: bold;
        padding: 0 1;
        background: $surface-lighten-1;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "select_account", "Switch", show=False),
        Binding("x", "remove_account", "Remove"),
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Switch Account", id="switcher-title")
        yield ListView(id="account-list")
        yield Static("enter to switch, x to remove, q to go back", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._build_list()

    def _build_list(self) -> None:
        from bluesky_tui.config import load_accounts

        lv = self.query_one("#account-list", ListView)
        lv.clear()

        data = load_accounts()
        active = data.get("active")

        for acct in data.get("accounts", []):
            lv.append(AccountItem(acct["handle"], acct["handle"] == active))

        lv.append(AddAccountItem())

    def action_cursor_down(self) -> None:
        self.query_one("#account-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#account-list", ListView).action_cursor_up()

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        self._handle_selection(event.item)

    def action_select_account(self) -> None:
        lv = self.query_one("#account-list", ListView)
        child = lv.highlighted_child
        if child:
            self._handle_selection(child)

    def _handle_selection(self, item: ListItem) -> None:
        if isinstance(item, AddAccountItem):
            from bluesky_tui.screens.login import LoginScreen
            self.app.push_screen(LoginScreen())
            return

        if isinstance(item, AccountItem):
            self._switch_to(item.handle)

    @work
    async def _switch_to(self, handle: str) -> None:
        from bluesky_tui.config import set_active_account, load_accounts

        set_active_account(handle)

        # Find the credentials for this account
        data = load_accounts()
        creds = None
        for acct in data["accounts"]:
            if acct["handle"] == handle:
                creds = acct
                break

        if not creds:
            self.app.notify("Account not found.", severity="error")
            return

        # Create a fresh client and log in
        from bluesky_tui.api.client import BlueskyClient

        new_client = BlueskyClient()
        try:
            await new_client.login(creds["handle"], creds["app_password"])
        except Exception as e:
            self.app.notify(f"Login failed: {e}", severity="error")
            return

        self.app.client = new_client
        from bluesky_tui.screens.feed import FeedScreen
        self.app.switch_screen(FeedScreen())

    def action_remove_account(self) -> None:
        lv = self.query_one("#account-list", ListView)
        child = lv.highlighted_child
        if not isinstance(child, AccountItem):
            return
        self._confirm_remove(child.handle)

    def _confirm_remove(self, handle: str) -> None:
        from textual.widgets import Button
        from textual.containers import Horizontal
        from textual.screen import ModalScreen

        class ConfirmRemove(ModalScreen[bool]):
            CSS = """
            ConfirmRemove {
                align: center middle;
            }
            #confirm-box {
                width: 50;
                height: auto;
                padding: 2 4;
                border: thick $accent;
                background: $surface;
            }
            #confirm-title {
                text-align: center;
                text-style: bold;
                margin-bottom: 1;
            }
            #confirm-buttons {
                width: 100%;
                height: 3;
                align: center middle;
            }
            #confirm-buttons Button {
                margin: 0 1;
            }
            """

            BINDINGS = [
                Binding("y", "confirm", "Yes"),
                Binding("n", "cancel", "No"),
                Binding("escape", "cancel", "Cancel"),
            ]

            def __init__(self, handle: str) -> None:
                super().__init__()
                self._handle = handle

            def compose(self) -> ComposeResult:
                from textual.containers import Center, Vertical
                with Center():
                    with Vertical(id="confirm-box"):
                        yield Static(
                            f"Remove @{self._handle}?",
                            id="confirm-title",
                        )
                        with Horizontal(id="confirm-buttons"):
                            yield Button("Yes (y)", variant="error", id="yes-btn")
                            yield Button("No (n)", variant="primary", id="no-btn")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss(event.button.id == "yes-btn")

            def action_confirm(self) -> None:
                self.dismiss(True)

            def action_cancel(self) -> None:
                self.dismiss(False)

        def on_result(confirmed: bool) -> None:
            if confirmed:
                from bluesky_tui.config import remove_account
                remove_account(handle)
                self._build_list()
                self.app.notify(f"Removed @{handle}")

        self.app.push_screen(ConfirmRemove(handle), callback=on_result)

    def action_go_back(self) -> None:
        self.app.pop_screen()
