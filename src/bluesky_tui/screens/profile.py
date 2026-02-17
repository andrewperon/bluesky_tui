from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView

from bluesky_tui.widgets.post import PostWidget
from bluesky_tui.widgets.post_list import PostList
from bluesky_tui.widgets.user_header import UserHeader
from bluesky_tui.api.models import ProfileData


class ProfileScreen(Screen):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("f", "toggle_follow", "Follow/Unfollow"),
        Binding("t", "view_thread", "Thread"),
        Binding("l", "toggle_like", "Like"),
        Binding("w", "view_on_web", "Web"),
        Binding("space", "load_more", "More", show=False),
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self, did: str) -> None:
        super().__init__()
        self._did = did
        self._profile: ProfileData | None = None
        self._cursor: str | None = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Loading profile...", id="profile-header-placeholder")
        yield PostList(id="profile-posts")
        yield Static("", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        if self.app.settings.get("post_density") == "compact":
            self.add_class("compact-density")
        self._load_profile()

    @work
    async def _load_profile(self) -> None:
        try:
            self._profile = await self.app.client.get_profile(self._did)
            placeholder = self.query_one("#profile-header-placeholder", Static)
            header = UserHeader(self._profile, id="profile-header")
            self.mount(header, before=placeholder)
            placeholder.remove()

            limit = self.app.settings.get("posts_per_page", 30)
            posts, cursor = await self.app.client.get_author_feed(self._did, limit=limit)
            self._cursor = cursor
            self.query_one("#profile-posts", PostList).set_posts(posts)
        except Exception as e:
            self.query_one("#status-bar", Static).update(f"Error: {e}")

    def action_cursor_down(self) -> None:
        self.query_one("#profile-posts", PostList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#profile-posts", PostList).action_cursor_up()

    def action_toggle_follow(self) -> None:
        self._toggle_follow()

    @work
    async def _toggle_follow(self) -> None:
        if not self._profile:
            return
        try:
            if self._profile.is_following and self._profile.follow_uri:
                await self.app.client.unfollow(self._profile.follow_uri)
                self._profile.is_following = False
                self._profile.follow_uri = None
                self.app.notify(f"Unfollowed @{self._profile.handle}")
            else:
                uri = await self.app.client.follow(self._profile.did)
                self._profile.is_following = True
                self._profile.follow_uri = uri
                self.app.notify(f"Followed @{self._profile.handle}")
            # Refresh header
            try:
                header = self.query_one("#profile-header", UserHeader)
                header.update_profile(self._profile)
            except Exception:
                pass
        except Exception as e:
            self.app.notify(f"Follow action failed: {e}", severity="error")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, PostWidget) and event.item.post_data:
            from bluesky_tui.screens.thread import ThreadScreen
            self.app.push_screen(ThreadScreen(event.item.post_data.uri))

    def action_view_thread(self) -> None:
        post_list = self.query_one("#profile-posts", PostList)
        post = post_list.selected_post
        if post:
            from bluesky_tui.screens.thread import ThreadScreen
            self.app.push_screen(ThreadScreen(post.uri))

    def action_toggle_like(self) -> None:
        self._toggle_like()

    @work
    async def _toggle_like(self) -> None:
        post_list = self.query_one("#profile-posts", PostList)
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
            except Exception:
                data.is_liked = True
                data.like_count += 1
                data.like_uri = old_uri
                widget.post_data = data
                widget._refresh_display()
        else:
            data.is_liked = True
            data.like_count += 1
            widget.post_data = data
            widget._refresh_display()
            try:
                like_uri = await self.app.client.like(data.uri, data.cid)
                data.like_uri = like_uri
                widget.post_data = data
            except Exception:
                data.is_liked = False
                data.like_count = max(0, data.like_count - 1)
                widget.post_data = data
                widget._refresh_display()

    def action_load_more(self) -> None:
        self._load_more()

    @work
    async def _load_more(self) -> None:
        if not self._cursor:
            return
        try:
            limit = self.app.settings.get("posts_per_page", 30)
            posts, cursor = await self.app.client.get_author_feed(self._did, cursor=self._cursor, limit=limit)
            self._cursor = cursor
            self.query_one("#profile-posts", PostList).append_posts(posts)
        except Exception as e:
            self.app.notify(f"Failed to load more: {e}", severity="error")

    def action_view_on_web(self) -> None:
        import webbrowser
        post_list = self.query_one("#profile-posts", PostList)
        post = post_list.selected_post
        if post:
            webbrowser.open(post.web_url)

    def action_go_back(self) -> None:
        self.app.pop_screen()
