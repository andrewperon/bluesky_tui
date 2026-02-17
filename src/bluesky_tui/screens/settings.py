from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView, ListItem


THEMES = ["textual-dark", "textual-light", "textual-ansi"]
DENSITIES = ["normal", "compact"]
FILTERS = ["all", "posts only", "text only"]
POSTS_PER_PAGE = [15, 30, 50]
NOTIFICATION_TYPES = ["like", "repost", "reply", "follow", "mention", "quote"]


class SettingItem(ListItem):
    """A single setting row: label + current value."""

    def __init__(self, key: str, label: str, value: str) -> None:
        super().__init__()
        self.setting_key = key
        self.setting_label = label
        self.setting_value = value

    def compose(self) -> ComposeResult:
        yield Static(self._render_text(), classes="setting-text")

    def _render_text(self) -> str:
        return f"  {self.setting_label}    [{self.setting_value}]"

    def update_value(self, value: str) -> None:
        self.setting_value = value
        self.query_one(".setting-text", Static).update(self._render_text())


class SectionHeader(ListItem):
    """Non-interactive section header."""

    def __init__(self, title: str) -> None:
        super().__init__()
        self.can_focus = False
        self._title = title

    def compose(self) -> ComposeResult:
        yield Static(self._title, classes="section-header-text")


class SettingsScreen(Screen):
    CSS = """
    SettingsScreen ListView {
        background: $background;
    }
    SettingsScreen ListView > ListItem {
        padding: 0;
        height: 1;
        background: $background;
    }
    SettingsScreen ListView > ListItem.--highlight {
        background: $accent;
    }
    .section-header-text {
        text-style: bold;
        color: $accent;
        padding: 0 1;
    }
    .setting-text {
        padding: 0 1;
    }
    #settings-title {
        text-style: bold;
        padding: 0 1;
        background: $surface-lighten-1;
        height: 1;
    }
    """

    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "toggle_setting", "Change"),
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._settings: dict = {}

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Settings", id="settings-title")
        yield ListView(id="settings-list")
        yield Static("j/k navigate, enter to change, q to go back", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        import copy
        self._settings = copy.deepcopy(self.app.settings)
        self._build_list()

    def _build_list(self) -> None:
        lv = self.query_one("#settings-list", ListView)
        lv.clear()

        s = self._settings

        # Account section
        lv.append(SectionHeader("── Account ──"))
        handle = "unknown"
        if self.app.client.me:
            name = self.app.client.me.display_name or self.app.client.me.handle
            handle = f"{name} (@{self.app.client.me.handle})"
        lv.append(SettingItem("account_info", "Logged in as", handle))
        lv.append(SettingItem("log_out", "Log out", "press enter"))

        # Display section
        lv.append(SectionHeader("── Display ──"))
        lv.append(SettingItem("theme", "Theme", s["theme"]))
        lv.append(SettingItem("post_density", "Post density", s["post_density"]))

        # Feed Defaults section
        lv.append(SectionHeader("── Feed Defaults ──"))
        lv.append(SettingItem("default_filter", "Default filter", s["default_filter"]))
        lv.append(SettingItem("posts_per_page", "Posts per page", str(s["posts_per_page"])))

        # Notifications section
        lv.append(SectionHeader("── Notifications ──"))
        nf = s["notification_filters"]
        for ntype in NOTIFICATION_TYPES:
            enabled = nf.get(ntype, True)
            lv.append(SettingItem(
                f"notif_{ntype}",
                f"Show {ntype}s",
                "on" if enabled else "off",
            ))

    def action_cursor_down(self) -> None:
        lv = self.query_one("#settings-list", ListView)
        lv.action_cursor_down()
        # Skip section headers
        child = lv.highlighted_child
        if isinstance(child, SectionHeader):
            lv.action_cursor_down()

    def action_cursor_up(self) -> None:
        lv = self.query_one("#settings-list", ListView)
        lv.action_cursor_up()
        child = lv.highlighted_child
        if isinstance(child, SectionHeader):
            lv.action_cursor_up()

    def action_toggle_setting(self) -> None:
        lv = self.query_one("#settings-list", ListView)
        child = lv.highlighted_child
        if not isinstance(child, SettingItem):
            return

        key = child.setting_key

        if key == "account_info":
            return

        if key == "log_out":
            self._confirm_logout()
            return

        if key == "theme":
            current = self._settings["theme"]
            idx = THEMES.index(current) if current in THEMES else 0
            new_val = THEMES[(idx + 1) % len(THEMES)]
            self._settings["theme"] = new_val
            child.update_value(new_val)
            self.app.theme = new_val
            self._save()
            return

        if key == "post_density":
            current = self._settings["post_density"]
            idx = DENSITIES.index(current) if current in DENSITIES else 0
            new_val = DENSITIES[(idx + 1) % len(DENSITIES)]
            self._settings["post_density"] = new_val
            child.update_value(new_val)
            self._save()
            return

        if key == "default_filter":
            current = self._settings["default_filter"]
            idx = FILTERS.index(current) if current in FILTERS else 0
            new_val = FILTERS[(idx + 1) % len(FILTERS)]
            self._settings["default_filter"] = new_val
            child.update_value(new_val)
            self._save()
            return

        if key == "posts_per_page":
            current = self._settings["posts_per_page"]
            idx = POSTS_PER_PAGE.index(current) if current in POSTS_PER_PAGE else 0
            new_val = POSTS_PER_PAGE[(idx + 1) % len(POSTS_PER_PAGE)]
            self._settings["posts_per_page"] = new_val
            child.update_value(str(new_val))
            self._save()
            return

        if key.startswith("notif_"):
            ntype = key[len("notif_"):]
            nf = self._settings["notification_filters"]
            nf[ntype] = not nf.get(ntype, True)
            child.update_value("on" if nf[ntype] else "off")
            self._save()
            return

    def _save(self) -> None:
        from bluesky_tui.config import save_settings
        self.app.settings = self._settings
        save_settings(self._settings)

    def _confirm_logout(self) -> None:
        from textual.widgets import Button
        from textual.containers import Horizontal
        from textual.screen import ModalScreen

        class ConfirmLogout(ModalScreen[bool]):
            CSS = """
            ConfirmLogout {
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

            def compose(self) -> ComposeResult:
                from textual.containers import Center, Vertical
                with Center():
                    with Vertical(id="confirm-box"):
                        yield Static("Are you sure you want to log out?", id="confirm-title")
                        with Horizontal(id="confirm-buttons"):
                            yield Button("Yes (y)", variant="error", id="yes-btn")
                            yield Button("No (n)", variant="primary", id="no-btn")

            def on_button_pressed(self, event: Button.Pressed) -> None:
                self.dismiss(event.button.id == "yes-btn")

            def action_confirm(self) -> None:
                self.dismiss(True)

            def action_cancel(self) -> None:
                self.dismiss(False)

        def handle_logout(confirmed: bool) -> None:
            if confirmed:
                from bluesky_tui.config import clear_credentials
                clear_credentials()
                from bluesky_tui.screens.login import LoginScreen
                self.app.switch_screen(LoginScreen())

        self.app.push_screen(ConfirmLogout(), callback=handle_logout)

    def action_go_back(self) -> None:
        self.app.pop_screen()
