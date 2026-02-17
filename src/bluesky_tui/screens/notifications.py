from __future__ import annotations

from textual import work
from textual.app import ComposeResult
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Header, Footer, Static, ListView

from bluesky_tui.api.models import NotificationData
from bluesky_tui.widgets.notification_item import (
    NotificationItem,
    GroupedNotificationItem,
)


def _group_notifications(
    notifications: list[NotificationData],
) -> list[NotificationItem | GroupedNotificationItem]:
    """Group consecutive like/repost notifications on the same subject into one item."""
    items: list[NotificationItem | GroupedNotificationItem] = []
    i = 0
    while i < len(notifications):
        n = notifications[i]
        # Only group likes and reposts
        if n.reason in ("like", "like-via-repost", "repost") and n.subject_uri:
            group = [n]
            j = i + 1
            while j < len(notifications):
                m = notifications[j]
                if m.reason == n.reason and m.subject_uri == n.subject_uri:
                    group.append(m)
                    j += 1
                else:
                    break
            if len(group) > 1:
                items.append(GroupedNotificationItem(group))
            else:
                items.append(NotificationItem(n))
            i = j
        else:
            items.append(NotificationItem(n))
            i += 1
    return items


class NotificationsScreen(Screen):
    BINDINGS = [
        Binding("j", "cursor_down", "Down", show=False),
        Binding("k", "cursor_up", "Up", show=False),
        Binding("enter", "open_notification", "Open"),
        Binding("p", "view_profile", "Profile"),
        Binding("R", "refresh_notifications", "Refresh"),
        Binding("space", "load_more", "More", show=False),
        Binding("escape", "go_back", "Back"),
        Binding("q", "go_back", "Back"),
    ]

    def __init__(self) -> None:
        super().__init__()
        self._cursor: str | None = None
        self._all_notifications: list[NotificationData] = []

    def compose(self) -> ComposeResult:
        yield Header()
        yield Static("Notifications", id="notif-title")
        yield ListView(id="notif-list")
        yield Static("Loading...", id="status-bar")
        yield Footer()

    def on_mount(self) -> None:
        self._load_notifications()

    def _update_title(self) -> None:
        unread = sum(1 for n in self._all_notifications if not n.is_read)
        title = self.query_one("#notif-title", Static)
        if unread:
            title.update(f"Notifications ({unread} unread)")
        else:
            title.update("Notifications")

    def _filter_by_type(self, notifications: list[NotificationData]) -> list[NotificationData]:
        nf = self.app.settings.get("notification_filters", {})
        def _is_enabled(n: NotificationData) -> bool:
            reason = n.reason
            # "like-via-repost" follows the "like" filter toggle
            if reason == "like-via-repost":
                reason = "like"
            return nf.get(reason, True)
        return [n for n in notifications if _is_enabled(n)]

    def _rebuild_list(self) -> None:
        notif_list = self.query_one("#notif-list", ListView)
        notif_list.clear()
        filtered = self._filter_by_type(self._all_notifications)
        items = _group_notifications(filtered)
        for item in items:
            notif_list.append(item)

    @work
    async def _load_notifications(self) -> None:
        status = self.query_one("#status-bar", Static)
        status.update("Loading notifications...")
        try:
            notifications, cursor = await self.app.client.get_notifications()
            self._cursor = cursor
            self._all_notifications = notifications
            self._update_title()
            self._rebuild_list()
            await self.app.client.mark_notifications_read()
            status.update("")
        except Exception as e:
            status.update(f"Error: {e}")

    def action_cursor_down(self) -> None:
        self.query_one("#notif-list", ListView).action_cursor_down()

    def action_cursor_up(self) -> None:
        self.query_one("#notif-list", ListView).action_cursor_up()

    def _open_notification(self, child: NotificationItem | GroupedNotificationItem) -> None:
        data = child.data
        if not data:
            return
        if data.reason == "like-via-repost" and data.subject_uri:
            self._open_repost_notification(data.subject_uri)
        elif data.reason in ("like", "repost", "reply", "mention", "quote") and data.subject_uri:
            from bluesky_tui.screens.thread import ThreadScreen
            self.app.push_screen(ThreadScreen(data.subject_uri))
        elif data.reason == "follow":
            from bluesky_tui.screens.profile import ProfileScreen
            self.app.push_screen(ProfileScreen(data.author_did))

    @work
    async def _open_repost_notification(self, repost_uri: str) -> None:
        post_uri = await self.app.client.resolve_repost_uri(repost_uri)
        if post_uri:
            from bluesky_tui.screens.thread import ThreadScreen
            self.app.push_screen(ThreadScreen(post_uri))
        else:
            self.app.notify("Could not resolve repost to original post.", severity="warning")

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if isinstance(event.item, (NotificationItem, GroupedNotificationItem)):
            self._open_notification(event.item)

    def action_open_notification(self) -> None:
        notif_list = self.query_one("#notif-list", ListView)
        child = notif_list.highlighted_child
        if isinstance(child, (NotificationItem, GroupedNotificationItem)):
            self._open_notification(child)

    def action_view_profile(self) -> None:
        notif_list = self.query_one("#notif-list", ListView)
        child = notif_list.highlighted_child
        if child and isinstance(child, (NotificationItem, GroupedNotificationItem)):
            from bluesky_tui.screens.profile import ProfileScreen
            self.app.push_screen(ProfileScreen(child.data.author_did))

    def action_refresh_notifications(self) -> None:
        self._cursor = None
        self._all_notifications.clear()
        self._load_notifications()

    def action_load_more(self) -> None:
        self._load_more()

    @work
    async def _load_more(self) -> None:
        if not self._cursor:
            self.app.notify("No more notifications.")
            return
        status = self.query_one("#status-bar", Static)
        status.update("Loading more...")
        try:
            notifications, cursor = await self.app.client.get_notifications(cursor=self._cursor)
            self._cursor = cursor
            self._all_notifications.extend(notifications)
            self._update_title()
            self._rebuild_list()
            status.update("")
        except Exception as e:
            self.app.notify(f"Failed to load more: {e}", severity="error")
            status.update("")

    def action_go_back(self) -> None:
        self.app.pop_screen()
