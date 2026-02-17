from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView

from bluesky_tui.api.models import PostData
from bluesky_tui.widgets.post_list import PostList
from bluesky_tui.widgets.post import PostWidget

FILTERS = ["all", "posts only", "text only"]


class FeedScreen(Screen):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("l", "toggle_like", "Like"),
        Binding("b", "toggle_repost", "Repost"),
        Binding("t", "view_thread", "Thread"),
        Binding("r", "reply", "Reply"),
        Binding("c", "compose", "Compose"),
        Binding("p", "view_profile", "Profile"),
        Binding("w", "view_on_web", "Web"),
        Binding("d", "delete_post", "Delete"),
        Binding("u", "my_profile", "Me"),
        Binding("n", "notifications", "Notifs"),
        Binding("m", "messages", "Messages"),
        Binding("s", "settings", "Settings"),
        Binding("f", "cycle_filter", "Filter"),
        Binding("space", "load_more", "More", show=False),
        Binding("R", "refresh_feed", "Refresh"),
        Binding("a", "switch_account", "Accounts"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._cursor: str | None = None
        self._all_posts: list[PostData] = []
        self._filter_index: int = 0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Filter: all", id="filter-bar")
        yield PostList(id="feed-list")
        yield Static("Loading timeline...", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        default_filter = self.app.settings.get("default_filter", "all")
        if default_filter in FILTERS:
            self._filter_index = FILTERS.index(default_filter)
        if self.app.settings.get("post_density") == "compact":
            self.add_class("compact-density")
        self._load_timeline()

    def _apply_filter(self, posts: list[PostData]) -> list[PostData]:
        f = FILTERS[self._filter_index]
        if f == "posts only":
            return [p for p in posts if not p.reason_repost_by and not p.reply_parent_uri]
        elif f == "text only":
            return [p for p in posts if not p.has_image and not p.has_video]
        return posts

    def _refresh_list(self) -> None:
        filtered = self._apply_filter(self._all_posts)
        self.query_one("#feed-list", PostList).set_posts(filtered)
        label = FILTERS[self._filter_index]
        self.query_one("#filter-bar", Static).update(f"Filter: {label}")

    def action_cycle_filter(self) -> None:
        self._filter_index = (self._filter_index + 1) % len(FILTERS)
        self._refresh_list()
        self.app.notify(f"Filter: {FILTERS[self._filter_index]}")

    @work
    async def _load_timeline(self) -> None:
        status = self.query_one("#status-bar", Static)
        status.update("Loading timeline...")
        try:
            limit = self.app.settings.get("posts_per_page", 30)
            posts, cursor = await self.app.client.get_timeline(limit=limit)
            self._cursor = cursor
            self._all_posts = posts
            self._refresh_list()
            status.update("")
        except Exception as e:
            status.update(f"Error: {e}")
            self.app.notify(f"Failed to load timeline: {e}", severity="error")

    def action_cursor_down(self) -> None:
        self.query_one("#feed-list", PostList).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#feed-list", PostList).action_cursor_up()

    def action_toggle_like(self) -> None:
        self._toggle_like()

    @work
    async def _toggle_like(self) -> None:
        post_list = self.query_one("#feed-list", PostList)
        widget = post_list.selected_widget
        if not widget or not widget.post_data:
            return
        data = widget.post_data

        if data.is_liked:
            # Optimistic unlike
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
            # Optimistic like
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

    def action_toggle_repost(self) -> None:
        self._toggle_repost()

    @work
    async def _toggle_repost(self) -> None:
        post_list = self.query_one("#feed-list", PostList)
        widget = post_list.selected_widget
        if not widget or not widget.post_data:
            return
        data = widget.post_data

        if data.is_reposted:
            old_uri = data.repost_uri
            data.is_reposted = False
            data.repost_count = max(0, data.repost_count - 1)
            data.repost_uri = None
            widget.post_data = data
            widget._refresh_display()
            try:
                if old_uri:
                    await self.app.client.unrepost(old_uri)
            except Exception as e:
                data.is_reposted = True
                data.repost_count += 1
                data.repost_uri = old_uri
                widget.post_data = data
                widget._refresh_display()
                self.app.notify(f"Unrepost failed: {e}", severity="error")
        else:
            data.is_reposted = True
            data.repost_count += 1
            widget.post_data = data
            widget._refresh_display()
            try:
                repost_uri = await self.app.client.repost(data.uri, data.cid)
                data.repost_uri = repost_uri
                widget.post_data = data
            except Exception as e:
                data.is_reposted = False
                data.repost_count = max(0, data.repost_count - 1)
                widget.post_data = data
                widget._refresh_display()
                self.app.notify(f"Repost failed: {e}", severity="error")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, PostWidget) and event.item.post_data:
            from bluesky_tui.screens.thread import ThreadScreen
            self.app.push_screen(ThreadScreen(event.item.post_data.uri))

    def action_view_thread(self) -> None:
        post_list = self.query_one("#feed-list", PostList)
        post = post_list.selected_post
        if post:
            from bluesky_tui.screens.thread import ThreadScreen
            self.app.push_screen(ThreadScreen(post.uri))

    def action_reply(self) -> None:
        post_list = self.query_one("#feed-list", PostList)
        post = post_list.selected_post
        if post:
            from bluesky_tui.screens.compose import ComposeScreen
            self.app.push_screen(ComposeScreen(reply_to=post))

    def action_compose(self) -> None:
        from bluesky_tui.screens.compose import ComposeScreen
        self.app.push_screen(ComposeScreen())

    def action_view_profile(self) -> None:
        post_list = self.query_one("#feed-list", PostList)
        post = post_list.selected_post
        if post:
            from bluesky_tui.screens.profile import ProfileScreen
            self.app.push_screen(ProfileScreen(post.author_did))

    def action_view_on_web(self) -> None:
        import webbrowser
        post_list = self.query_one("#feed-list", PostList)
        post = post_list.selected_post
        if post:
            webbrowser.open(post.web_url)

    def action_delete_post(self) -> None:
        self._delete_post()

    @work
    async def _delete_post(self) -> None:
        post_list = self.query_one("#feed-list", PostList)
        widget = post_list.selected_widget
        if not widget or not widget.post_data:
            return
        data = widget.post_data
        if not self.app.client.me or data.author_did != self.app.client.me.did:
            self.app.notify("You can only delete your own posts.", severity="warning")
            return
        try:
            await self.app.client.delete_post(data.uri)
            post_list.remove_children([widget])
            self.app.notify("Post deleted.")
        except Exception as e:
            self.app.notify(f"Delete failed: {e}", severity="error")

    def action_load_more(self) -> None:
        self._load_more()

    @work
    async def _load_more(self) -> None:
        if not self._cursor:
            self.app.notify("No more posts to load.")
            return
        status = self.query_one("#status-bar", Static)
        status.update("Loading more...")
        try:
            limit = self.app.settings.get("posts_per_page", 30)
            posts, cursor = await self.app.client.get_timeline(cursor=self._cursor, limit=limit)
            self._cursor = cursor
            self._all_posts.extend(posts)
            filtered = self._apply_filter(posts)
            self.query_one("#feed-list", PostList).append_posts(filtered)
            status.update("")
        except Exception as e:
            status.update(f"Error: {e}")

    def action_refresh_feed(self) -> None:
        self._cursor = None
        self._all_posts.clear()
        self._load_timeline()

    def action_my_profile(self) -> None:
        if self.app.client.me:
            from bluesky_tui.screens.profile import ProfileScreen
            self.app.push_screen(ProfileScreen(self.app.client.me.did))

    def action_notifications(self) -> None:
        from bluesky_tui.screens.notifications import NotificationsScreen
        self.app.push_screen(NotificationsScreen())

    def action_messages(self) -> None:
        from bluesky_tui.screens.conversations import ConversationsScreen
        self.app.push_screen(ConversationsScreen())

    def action_switch_account(self) -> None:
        from bluesky_tui.screens.account_switcher import AccountSwitcherScreen
        self.app.push_screen(AccountSwitcherScreen())

    def action_settings(self) -> None:
        from bluesky_tui.screens.settings import SettingsScreen
        self.app.push_screen(SettingsScreen())
