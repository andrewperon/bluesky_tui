from __future__ import annotations

from textual.app import ComposeResult
from textual.widgets import ListView

from bluesky_tui.api.models import PostData
from bluesky_tui.widgets.post import PostWidget


class PostList(ListView):
    CSS = """
    PostList {
        height: 1fr;
    }
    """

    def set_posts(self, posts: list[PostData]) -> None:
        self.clear()
        for post in posts:
            self.append(PostWidget(post))

    def append_posts(self, posts: list[PostData]) -> None:
        for post in posts:
            self.append(PostWidget(post))

    @property
    def selected_post(self) -> PostData | None:
        if self.highlighted_child and isinstance(self.highlighted_child, PostWidget):
            return self.highlighted_child.post_data
        return None

    @property
    def selected_widget(self) -> PostWidget | None:
        if self.highlighted_child and isinstance(self.highlighted_child, PostWidget):
            return self.highlighted_child
        return None
