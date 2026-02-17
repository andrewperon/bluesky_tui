from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView

from bluesky_tui.widgets.post import PostWidget
from bluesky_tui.widgets.post_list import PostList


class ThreadScreen(Screen):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("l", "toggle_like", "Like"),
        Binding("r", "reply", "Reply"),
        Binding("p", "view_profile", "Profile"),
        Binding("w", "view_on_web", "Web"),
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self, post_uri: str) -> None:
        super().__init__()
        self._post_uri = post_uri

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Thread", id="thread-title")
        yield PostList(id="thread-list")
        yield Static("Loading thread...", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        if self.app.settings.get("post_density") == "compact":
            self.add_class("compact-density")
        self._load_thread()

    @work
    async def _load_thread(self) -> None:
        status = self.query_one("#status-bar", Static)
        status.update("Loading thread...")
        try:
            thread = await self.app.client.get_post_thread(self._post_uri)
            post_list = self.query_one("#thread-list", PostList)
            all_posts = []
            for parent in thread.parents:
                all_posts.append(parent)
            if thread.post:
                all_posts.append(thread.post)
            for reply in thread.replies:
                all_posts.append(reply)
            post_list.set_posts(all_posts)

            # Highlight the main post
            main_idx = len(thread.parents)
            if main_idx < len(post_list.children):
                post_list.index = main_idx

            status.update("")
        except Exception as e:
            status.update(f"Error: {e}")
            self.app.notify(f"Failed to load thread: {e}", severity="error")

    def action_cursor_down(self) -> None:
        self.query_one("#thread-list", PostList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#thread-list", PostList).action_cursor_up()

    def action_toggle_like(self) -> None:
        self._toggle_like()

    @work
    async def _toggle_like(self) -> None:
        post_list = self.query_one("#thread-list", PostList)
        widget = post_list.selected_widget
        if not widget or not widget.post_data:
            return
        data = widget.post_data

        if data.is_liked:
            old_uri = data.like_uri
            data.is_liked = False
            data.like_count = max(0, data.like_count - 1)
            data.like_uri = None
            widget.post_data = data
            widget._refresh_display()
            try:
                if old_uri:
                    await self.app.client.unlike(old_uri)
            except Exception as e:
                data.is_liked = True
                data.like_count += 1
                data.like_uri = old_uri
                widget.post_data = data
                widget._refresh_display()
                self.app.notify(f"Unlike failed: {e}", severity="error")
        else:
            data.is_liked = True
            data.like_count += 1
            widget.post_data = data
            widget._refresh_display()
            try:
                like_uri = await self.app.client.like(data.uri, data.cid)
                data.like_uri = like_uri
                widget.post_data = data
            except Exception as e:
                data.is_liked = False
                data.like_count = max(0, data.like_count - 1)
                widget.post_data = data
                widget._refresh_display()
                self.app.notify(f"Like failed: {e}", severity="error")

    def action_reply(self) -> None:
        post_list = self.query_one("#thread-list", PostList)
        post = post_list.selected_post
        if post:
            from bluesky_tui.screens.compose import ComposeScreen
            self.app.push_screen(ComposeScreen(reply_to=post))

    def action_view_profile(self) -> None:
        post_list = self.query_one("#thread-list", PostList)
        post = post_list.selected_post
        if post:
            from bluesky_tui.screens.profile import ProfileScreen
            self.app.push_screen(ProfileScreen(post.author_did))

    def action_view_on_web(self) -> None:
        import webbrowser
        post_list = self.query_one("#thread-list", PostList)
        post = post_list.selected_post
        if post:
            webbrowser.open(post.web_url)

    def action_go_back(self) -> None:
        self.app.pop_screen()
