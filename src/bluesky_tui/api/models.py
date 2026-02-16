from __future__ import annotations

from dataclasses import dataclass


@dataclass
class PostData:
    uri: str  # at://did:plc:xxx/app.bsky.feed.post/rkey
    cid: str
    author_did: str
    author_handle: str
    author_display_name: str
    text: str
    created_at: str
    like_count: int
    repost_count: int
    reply_count: int
    is_liked: bool
    is_reposted: bool
    like_uri: str | None
    repost_uri: str | None
    reason_repost_by: str | None
    reply_parent_uri: str | None
    reply_parent_author: str | None
    reply_root_uri: str | None
    embed_type: str | None
    embed_text: str | None
    embed_author: str | None
    has_image: bool
    has_video: bool

    @property
    def web_url(self) -> str:
        rkey = self.uri.rsplit("/", 1)[-1]
        return f"https://bsky.app/profile/{self.author_handle}/post/{rkey}"


@dataclass
class ProfileData:
    did: str
    handle: str
    display_name: str
    description: str
    avatar_url: str
    followers_count: int
    following_count: int
    posts_count: int
    is_following: bool
    follow_uri: str | None


@dataclass
class ThreadData:
    parents: list[PostData]
    post: PostData | None
    replies: list[PostData]


@dataclass
class NotificationData:
    uri: str
    cid: str
    author_did: str
    author_handle: str
    author_display_name: str
    reason: str  # like, repost, follow, mention, reply, quote
    text: str
    created_at: str
    is_read: bool
    subject_uri: str
