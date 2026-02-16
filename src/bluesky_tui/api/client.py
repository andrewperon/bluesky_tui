from __future__ import annotations

from atproto import AsyncClient

from bluesky_tui.api.models import PostData, ProfileData, ThreadData, NotificationData


def _has_media(embed) -> tuple[bool, bool]:
    """Return (has_image, has_video) from a post embed."""
    if not embed:
        return False, False
    has_image = hasattr(embed, "images")
    has_video = hasattr(embed, "playlist") or hasattr(embed, "video")
    # RecordWithMedia embeds nest media inside .media
    if hasattr(embed, "media"):
        inner = embed.media
        has_image = has_image or hasattr(inner, "images")
        has_video = has_video or hasattr(inner, "playlist") or hasattr(inner, "video")
    return has_image, has_video


class BlueskyClient:
    def __init__(self):
        self._client = AsyncClient()
        self.me: ProfileData | None = None

    async def login(self, handle: str, app_password: str) -> None:
        profile = await self._client.login(handle, app_password)
        self.me = ProfileData(
            did=profile.did,
            handle=profile.handle,
            display_name=profile.display_name or profile.handle,
            description="",
            avatar_url=profile.avatar or "",
            followers_count=0,
            following_count=0,
            posts_count=0,
            is_following=False,
            follow_uri=None,
        )

    async def get_timeline(self, cursor: str | None = None) -> tuple[list[PostData], str | None]:
        resp = await self._client.get_timeline(cursor=cursor, limit=30)
        posts = []
        for item in resp.feed:
            post = item.post
            record = post.record
            # Determine if this is a repost
            reason_repost_by = None
            if item.reason and hasattr(item.reason, "by"):
                reason_repost_by = item.reason.by.handle

            viewer = post.viewer

            # Extract reply parent info
            reply_parent_uri = None
            reply_parent_author = None
            reply_root_uri = None
            if item.reply and hasattr(item.reply, "parent") and hasattr(item.reply.parent, "author"):
                reply_parent_uri = item.reply.parent.uri
                reply_parent_author = item.reply.parent.author.handle
            if item.reply and hasattr(item.reply, "root"):
                reply_root_uri = getattr(item.reply.root, "uri", None)

            posts.append(PostData(
                uri=post.uri,
                cid=post.cid,
                author_did=post.author.did,
                author_handle=post.author.handle,
                author_display_name=post.author.display_name or post.author.handle,
                text=record.text if hasattr(record, "text") else "",
                created_at=record.created_at if hasattr(record, "created_at") else "",
                like_count=post.like_count or 0,
                repost_count=post.repost_count or 0,
                reply_count=post.reply_count or 0,
                is_liked=bool(viewer and viewer.like),
                is_reposted=bool(viewer and viewer.repost),
                like_uri=viewer.like if viewer else None,
                repost_uri=viewer.repost if viewer else None,
                reason_repost_by=reason_repost_by,
                reply_parent_uri=reply_parent_uri,
                reply_parent_author=reply_parent_author,
                reply_root_uri=reply_root_uri,
                embed_type=None,
                embed_text=None,
                embed_author=None,
                has_image=_has_media(post.embed)[0],
                has_video=_has_media(post.embed)[1],
            ))
        return posts, resp.cursor

    async def like(self, uri: str, cid: str) -> str:
        resp = await self._client.like(uri, cid)
        return resp.uri

    async def unlike(self, like_uri: str) -> None:
        await self._client.unlike(like_uri)

    async def repost(self, uri: str, cid: str) -> str:
        resp = await self._client.repost(uri, cid)
        return resp.uri

    async def unrepost(self, repost_uri: str) -> None:
        await self._client.unrepost(repost_uri)

    async def delete_post(self, uri: str) -> None:
        await self._client.delete_post(uri)

    async def create_post(
        self,
        text: str,
        reply_to: PostData | None = None,
        quote: PostData | None = None,
    ) -> PostData:
        from atproto import models as atproto_models

        def _strong_ref(uri: str, cid: str):
            return atproto_models.ComAtprotoRepoStrongRef.Main(uri=uri, cid=cid)

        reply_ref = None
        if reply_to:
            root_uri = reply_to.reply_root_uri or reply_to.uri
            root_cid = reply_to.cid
            parent_ref = _strong_ref(reply_to.uri, reply_to.cid)
            root_ref = _strong_ref(root_uri, root_cid)
            reply_ref = atproto_models.AppBskyFeedPost.ReplyRef(
                parent=parent_ref,
                root=root_ref,
            )

        embed = None
        if quote:
            embed = atproto_models.AppBskyEmbedRecord.Main(
                record=_strong_ref(quote.uri, quote.cid),
            )

        resp = await self._client.send_post(
            text=text,
            reply_to=reply_ref,
            embed=embed,
        )
        return PostData(
            uri=resp.uri,
            cid=resp.cid,
            author_did=self.me.did if self.me else "",
            author_handle=self.me.handle if self.me else "",
            author_display_name=self.me.display_name if self.me else "",
            text=text,
            created_at="",
            like_count=0,
            repost_count=0,
            reply_count=0,
            is_liked=False,
            is_reposted=False,
            like_uri=None,
            repost_uri=None,
            reason_repost_by=None,
            reply_parent_uri=reply_to.uri if reply_to else None,
            reply_parent_author=reply_to.author_handle if reply_to else None,
            reply_root_uri=reply_to.reply_root_uri if reply_to else None,
            embed_type=None,
            embed_text=None,
            embed_author=None,
            has_image=False,
            has_video=False,
        )

    async def get_post_thread(self, uri: str) -> ThreadData:
        resp = await self._client.get_post_thread(uri, depth=10, parent_height=10)
        thread = resp.thread

        def _parse_thread_post(tv) -> PostData | None:
            if not hasattr(tv, "post"):
                return None
            post = tv.post
            record = post.record
            viewer = post.viewer
            return PostData(
                uri=post.uri,
                cid=post.cid,
                author_did=post.author.did,
                author_handle=post.author.handle,
                author_display_name=post.author.display_name or post.author.handle,
                text=record.text if hasattr(record, "text") else "",
                created_at=record.created_at if hasattr(record, "created_at") else "",
                like_count=post.like_count or 0,
                repost_count=post.repost_count or 0,
                reply_count=post.reply_count or 0,
                is_liked=bool(viewer and viewer.like),
                is_reposted=bool(viewer and viewer.repost),
                like_uri=viewer.like if viewer else None,
                repost_uri=viewer.repost if viewer else None,
                reason_repost_by=None,
                reply_parent_uri=None,
                reply_parent_author=None,
                reply_root_uri=None,
                embed_type=None,
                embed_text=None,
                embed_author=None,
                has_image=_has_media(post.embed)[0],
                has_video=_has_media(post.embed)[1],
            )

        # Collect parents
        parents = []
        node = thread
        while hasattr(node, "parent") and node.parent and hasattr(node.parent, "post"):
            p = _parse_thread_post(node.parent)
            if p:
                parents.insert(0, p)
            node = node.parent

        # Main post
        main_post = _parse_thread_post(thread)

        # Collect replies
        replies = []
        if hasattr(thread, "replies") and thread.replies:
            for reply_view in thread.replies:
                r = _parse_thread_post(reply_view)
                if r:
                    replies.append(r)

        return ThreadData(
            parents=parents,
            post=main_post,
            replies=replies,
        )

    async def get_profile(self, handle_or_did: str) -> ProfileData:
        p = await self._client.get_profile(handle_or_did)
        return ProfileData(
            did=p.did,
            handle=p.handle,
            display_name=p.display_name or p.handle,
            description=p.description or "",
            avatar_url=p.avatar or "",
            followers_count=p.followers_count or 0,
            following_count=p.follows_count or 0,
            posts_count=p.posts_count or 0,
            is_following=bool(p.viewer and p.viewer.following),
            follow_uri=p.viewer.following if p.viewer else None,
        )

    async def get_author_feed(self, did: str, cursor: str | None = None) -> tuple[list[PostData], str | None]:
        resp = await self._client.get_author_feed(did, cursor=cursor, limit=30)
        posts = []
        for item in resp.feed:
            post = item.post
            record = post.record
            viewer = post.viewer
            posts.append(PostData(
                uri=post.uri,
                cid=post.cid,
                author_did=post.author.did,
                author_handle=post.author.handle,
                author_display_name=post.author.display_name or post.author.handle,
                text=record.text if hasattr(record, "text") else "",
                created_at=record.created_at if hasattr(record, "created_at") else "",
                like_count=post.like_count or 0,
                repost_count=post.repost_count or 0,
                reply_count=post.reply_count or 0,
                is_liked=bool(viewer and viewer.like),
                is_reposted=bool(viewer and viewer.repost),
                like_uri=viewer.like if viewer else None,
                repost_uri=viewer.repost if viewer else None,
                reason_repost_by=None,
                reply_parent_uri=None,
                reply_parent_author=None,
                reply_root_uri=None,
                embed_type=None,
                embed_text=None,
                embed_author=None,
                has_image=_has_media(post.embed)[0],
                has_video=_has_media(post.embed)[1],
            ))
        return posts, resp.cursor

    async def follow(self, did: str) -> str:
        resp = await self._client.follow(did)
        return resp.uri

    async def unfollow(self, follow_uri: str) -> None:
        await self._client.unfollow(follow_uri)

    async def get_notifications(self, cursor: str | None = None) -> tuple[list[NotificationData], str | None]:
        resp = await self._client.app.bsky.notification.list_notifications(
            {"cursor": cursor, "limit": 30}
        )
        notifications = []
        for n in resp.notifications:
            # Extract text for reply/mention/quote notifications
            text = ""
            if hasattr(n, "record") and hasattr(n.record, "text"):
                text = n.record.text

            notifications.append(NotificationData(
                uri=n.uri,
                cid=n.cid,
                author_did=n.author.did,
                author_handle=n.author.handle,
                author_display_name=n.author.display_name or n.author.handle,
                reason=n.reason,
                text=text,
                created_at=n.indexed_at,
                is_read=n.is_read,
                subject_uri=n.reason_subject or "",
            ))
        return notifications, resp.cursor

    async def mark_notifications_read(self) -> None:
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc).isoformat()
        await self._client.app.bsky.notification.update_seen({"seen_at": now})
