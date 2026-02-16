from textual import work
from textual.app import ComposeResult
from textual.screen import Screen
from textual.widgets import Input, Button, Checkbox, Static, Header, Footer
from textual.containers import Center, Vertical


class LoginScreen(Screen):
    CSS = """
    LoginScreen {
        align: center middle;
    }
    #login-box {
        width: 60;
        height: auto;
        padding: 2 4;
        border: thick $accent;
        background: $surface;
    }
    #login-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    #login-error {
        color: $error;
        text-align: center;
        margin-top: 1;
        display: none;
    }
    #login-error.visible {
        display: block;
    }
    Input {
        margin-bottom: 1;
    }
    Button {
        width: 100%;
        margin-top: 1;
    }
    """

    def compose(self) -> ComposeResult:
        yield Header()
        with Center():
            with Vertical(id="login-box"):
                yield Static("Bluesky Login", id="login-title")
                yield Input(placeholder="Handle (e.g. user.bsky.social)", id="handle")
                yield Input(placeholder="App Password", id="app-password", password=True)
                yield Checkbox("Save credentials", id="save-creds", value=True)
                yield Button("Login", variant="primary", id="login-btn")
                yield Static("", id="login-error")
        yield Footer()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "login-btn":
            self._do_login()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        self._do_login()

    @work
    async def _do_login(self) -> None:
        handle_input = self.query_one("#handle", Input)
        password_input = self.query_one("#app-password", Input)
        error_label = self.query_one("#login-error", Static)
        login_btn = self.query_one("#login-btn", Button)
        save_checkbox = self.query_one("#save-creds", Checkbox)

        handle = handle_input.value.strip()
        password = password_input.value.strip()

        if not handle or not password:
            error_label.update("Please enter both handle and app password.")
            error_label.add_class("visible")
            return

        login_btn.disabled = True
        login_btn.label = "Logging in..."
        error_label.remove_class("visible")

        try:
            await self.app.client.login(handle, password)
            if save_checkbox.value:
                from bluesky_tui.config import save_credentials
                save_credentials(handle, password)
            from bluesky_tui.screens.feed import FeedScreen
            self.app.switch_screen(FeedScreen())
        except Exception as e:
            error_label.update(f"Login failed: {e}")
            error_label.add_class("visible")
            login_btn.disabled = False
            login_btn.label = "Login"
