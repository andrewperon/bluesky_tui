from __future__ import annotations

import uuid
from datetime import datetime, timezone, timedelta

from bluesky_tui.api.models import PostData, ProfileData, ThreadData, NotificationData, MessageData, ConversationData

# ---------------------------------------------------------------------------
# Mock users
# ---------------------------------------------------------------------------

_DEMO_USER = ("did:plc:demo000000000", "alice.bsky.social", "Alice Chen")

_USERS = [
    ("did:plc:demo000000001", "devjordan.bsky.social", "Jordan Rivera"),
    ("did:plc:demo000000002", "sarahcodes.bsky.social", "Sarah Park"),
    ("did:plc:demo000000003", "maxwelltech.bsky.social", "Max Okonkwo"),
    ("did:plc:demo000000004", "emilywrites.bsky.social", "Emily Zhang"),
    ("did:plc:demo000000005", "rustacean.dev", "Kai Ferretti"),
    ("did:plc:demo000000006", "webdev.maya.bsky.social", "Maya Johnson"),
    ("did:plc:demo000000007", "opensourcefan.bsky.social", "Leo Nakamura"),
]


def _ts(hours_ago: float) -> str:
    """Return an ISO timestamp for *hours_ago* hours before now."""
    dt = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return dt.isoformat()


def _uri(did: str, rkey: str) -> str:
    return f"at://{did}/app.bsky.feed.post/{rkey}"


def _cid(idx: int) -> str:
    return f"bafyreicid{idx:04d}"


# ---------------------------------------------------------------------------
# Build mock posts
# ---------------------------------------------------------------------------

_POST_DEFS: list[tuple[int, str, int, int, int, bool, bool, bool]] = [
    # (user_idx, text, likes, reposts, replies, is_liked, has_image, has_video)
    (-1, "Just released v2.0 of my AT Protocol library. Six months of work, 142 PRs merged. Huge thanks to every contributor!", 87, 23, 14, False, False, False),
    (0, "Hot take: the best programming language is the one your team already knows.", 214, 45, 38, True, False, False),
    (1, "The new React Server Components model finally clicked for me today. It's all about where the boundary lives between server and client.", 128, 31, 22, False, False, False),
    (2, "Anyone else feel like we're in the golden age of terminal apps? TUIs are having a moment and I'm here for it.", 95, 18, 12, True, False, False),
    (3, "Spent the weekend building a Bluesky bot that posts sunrise photos from around the world. The AT Protocol docs are surprisingly good.", 67, 11, 8, False, True, False),
    (4, "Unpopular opinion: CSS is a programming language. Fight me.", 312, 52, 87, False, False, False),
    (5, "Just hit 10k followers here on Bluesky. The community is genuinely different from anywhere else. More conversations, less dunking.", 156, 29, 19, True, False, False),
    (6, "TIL: you can use `git bisect` with a script to automatically find the commit that broke your tests. Absolute game changer.", 203, 67, 15, False, False, False),
    (-1, "Working on dark mode support for every component in the app. My eyes already thank me.", 42, 5, 7, False, False, False),
    (0, "Decentralized social media isn't just about moderation. It's about data ownership and portability. Your posts should be yours.", 178, 41, 26, False, False, False),
    (1, "The Textual framework for Python TUIs is incredible. Built a full app in a weekend. If you write Python you should try it.", 94, 22, 11, True, False, False),
    (2, "Just finished reading \"Designing Data-Intensive Applications\" for the third time. Every read reveals something new.", 115, 19, 9, False, True, False),
    (3, "Shipped a new feature today: inline code preview with syntax highlighting. Took way longer than expected but it looks great.", 53, 7, 4, False, False, False),
    (4, "Fun weekend project: I wrote a Rust CLI that fetches your Bluesky feed and renders it in the terminal. ~500 lines total.", 88, 15, 10, False, False, False),
    (5, "Reminder: you don't need a side project. You don't need to hustle. Rest is productive too.", 445, 112, 34, True, False, False),
    (6, "Open source maintainers don't owe you anything. Be kind, file good issues, and say thank you.", 267, 73, 21, False, False, False),
]


def _build_posts() -> list[PostData]:
    posts: list[PostData] = []
    now_hours = 0.5
    for idx, (user_idx, text, likes, reposts, replies, is_liked, has_img, has_vid) in enumerate(_POST_DEFS):
        if user_idx == -1:
            did, handle, display = _DEMO_USER
        else:
            did, handle, display = _USERS[user_idx]

        # Make one post a repost (index 7 reposted by user 3)
        reason_repost_by = None
        if idx == 7:
            reason_repost_by = _USERS[3][1]

        # Make one post a reply (index 12 replying to index 0)
        reply_parent_uri = None
        reply_parent_author = None
        reply_root_uri = None
        if idx == 12:
            reply_parent_uri = _uri(_DEMO_USER[0], "rkey0000")
            reply_parent_author = _DEMO_USER[1]
            reply_root_uri = reply_parent_uri

        posts.append(PostData(
            uri=_uri(did, f"rkey{idx:04d}"),
            cid=_cid(idx),
            author_did=did,
            author_handle=handle,
            author_display_name=display,
            text=text,
            created_at=_ts(now_hours),
            like_count=likes,
            repost_count=reposts,
            reply_count=replies,
            is_liked=is_liked,
            is_reposted=False,
            like_uri=f"at://{_DEMO_USER[0]}/app.bsky.feed.like/lk{idx:04d}" if is_liked else None,
            repost_uri=None,
            reason_repost_by=reason_repost_by,
            reply_parent_uri=reply_parent_uri,
            reply_parent_author=reply_parent_author,
            reply_root_uri=reply_root_uri,
            embed_type=None,
            embed_text=None,
            embed_author=None,
            has_image=has_img,
            has_video=has_vid,
        ))
        now_hours += 1.2
    return posts


# ---------------------------------------------------------------------------
# Build mock profiles
# ---------------------------------------------------------------------------

def _build_profiles() -> dict[str, ProfileData]:
    profiles: dict[str, ProfileData] = {}
    did, handle, display = _DEMO_USER
    profiles[did] = ProfileData(
        did=did,
        handle=handle,
        display_name=display,
        description="Software engineer. Building things for the open web. she/her",
        avatar_url="",
        followers_count=1247,
        following_count=483,
        posts_count=892,
        is_following=False,
        follow_uri=None,
    )
    descriptions = [
        "Full-stack dev. Coffee enthusiast. Always shipping.",
        "Frontend engineer at a startup. React, TypeScript, and too many side projects.",
        "Backend engineer. Distributed systems. Building the future one API at a time.",
        "Writer, coder, professional yak-shaver. Opinions are my own.",
        "Rust evangelist. Systems programming is my happy place.",
        "Web developer & designer. Making the internet prettier, one pixel at a time.",
        "Open source contributor. Believe in building in public.",
    ]
    for i, (u_did, u_handle, u_display) in enumerate(_USERS):
        profiles[u_did] = ProfileData(
            did=u_did,
            handle=u_handle,
            display_name=u_display,
            description=descriptions[i],
            avatar_url="",
            followers_count=[3421, 1893, 756, 2104, 4512, 1337, 982][i],
            following_count=[412, 302, 198, 567, 234, 445, 621][i],
            posts_count=[1203, 876, 432, 1567, 654, 998, 345][i],
            is_following=i < 4,
            follow_uri=f"at://{_DEMO_USER[0]}/app.bsky.graph.follow/fw{i:04d}" if i < 4 else None,
        )
    return profiles


# ---------------------------------------------------------------------------
# Build mock notifications
# ---------------------------------------------------------------------------

def _build_notifications(posts: list[PostData]) -> list[NotificationData]:
    notifs: list[NotificationData] = []
    subject = posts[0].uri if posts else ""
    defs = [
        (0, "like", "", False, subject),
        (1, "like", "", False, subject),
        (2, "like", "", False, subject),
        (3, "repost", "", False, subject),
        (4, "follow", "", False, ""),
        (5, "reply", "This is such a great take! I've been saying this for months.", True, subject),
        (6, "mention", f"@{_DEMO_USER[1]} have you seen the new Textual release? Thought of you.", True, ""),
        (0, "quote", "Couldn't agree more with this. Portability is the killer feature of decentralized protocols.", True, subject),
        (2, "follow", "", True, ""),
        (4, "reply", "Would love to see the source code for this! Any plans to open source it?", True, posts[8].uri if len(posts) > 8 else subject),
        (6, "like", "", True, posts[8].uri if len(posts) > 8 else subject),
    ]
    hours = 0.3
    for idx, (user_idx, reason, text, is_read, subj) in enumerate(defs):
        u_did, u_handle, u_display = _USERS[user_idx]
        notifs.append(NotificationData(
            uri=f"at://{u_did}/app.bsky.feed.post/notif{idx:04d}",
            cid=f"bafyreinotif{idx:04d}",
            author_did=u_did,
            author_handle=u_handle,
            author_display_name=u_display,
            reason=reason,
            text=text,
            created_at=_ts(hours),
            is_read=is_read,
            subject_uri=subj,
        ))
        hours += 0.8
    return notifs


# ---------------------------------------------------------------------------
# Build mock conversations + messages
# ---------------------------------------------------------------------------

_CONVO_IDS = ["convo0001", "convo0002", "convo0003"]


def _build_conversations_and_messages(
    demo_did: str,
) -> tuple[list[ConversationData], dict[str, list[MessageData]]]:
    demo_user_member = {"did": _DEMO_USER[0], "handle": _DEMO_USER[1], "display_name": _DEMO_USER[2]}

    convo_defs = [
        # (convo_idx, other_user_idx, unread_count, message_defs)
        # message_defs: list of (is_mine, text, hours_ago)
        (0, 0, 2, [
            (False, "Hey! Saw your post about the AT Protocol library — really impressive work.", 6.0),
            (True, "Thanks! It's been a wild ride. Six months feels like a lifetime in software time.", 5.8),
            (False, "Haha no kidding. Are you planning to add WebSocket support in the next version?", 5.5),
            (True, "That's actually on the roadmap for Q2. Want to collaborate on the spec?", 5.0),
            (False, "Absolutely, count me in. I'll DM you my calendar link.", 4.5),
            (True, "Perfect. Looking forward to it!", 4.0),
            (False, "Also — congrats on the 10k milestone! Huge deal.", 0.5),
            (True, "Ha, honestly didn't expect it to happen this fast. The community here is something else.", 0.2),
        ]),
        (1, 2, 0, [
            (False, "Hi Alice! Did you see the Textual 1.0 announcement?", 48.0),
            (True, "YES. I've been waiting for this. We should do a proper writeup.", 47.5),
            (False, "100%. I can draft the intro if you cover the new features?", 47.0),
            (True, "Deal. Let's sync up Thursday?", 46.5),
            (False, "Thursday works. I'll send a calendar invite.", 46.0),
            (True, "Great, see you then!", 45.5),
        ]),
        (2, 4, 1, [
            (False, "Quick question — what's your take on async vs threads for TUI apps?", 72.0),
            (True, "Async all the way. Threads with UI state are a debugging nightmare.", 71.5),
            (False, "Yeah, I figured. Had a gnarly race condition last week and it took me two days.", 71.0),
            (True, "Classic. What framework were you using?", 70.5),
            (False, "tkinter, don't judge me 😅", 70.0),
            (True, "No judgment! tkinter is fine for quick stuff. But if you want to go terminal, try Textual.", 69.5),
            (False, "Already on it after your post! This bluesky_tui project is great inspiration.", 1.0),
        ]),
    ]

    all_convos: list[ConversationData] = []
    all_messages: dict[str, list[MessageData]] = {}

    for convo_idx, other_user_idx, unread_count, msg_defs in convo_defs:
        convo_id = _CONVO_IDS[convo_idx]
        other = _USERS[other_user_idx]
        other_member = {"did": other[0], "handle": other[1], "display_name": other[2]}

        messages: list[MessageData] = []
        for i, (is_mine, text, hours_ago) in enumerate(msg_defs):
            sender = _DEMO_USER if is_mine else other
            messages.append(MessageData(
                id=f"{convo_id}_msg{i:04d}",
                convo_id=convo_id,
                sender_did=sender[0],
                sender_handle=sender[1],
                sender_display_name=sender[2],
                text=text,
                sent_at=_ts(hours_ago),
                is_mine=is_mine,
            ))

        last_msg = messages[-1] if messages else None
        all_convos.append(ConversationData(
            id=convo_id,
            members=[demo_user_member, other_member],
            last_message=last_msg,
            unread_count=unread_count,
            muted=False,
        ))
        all_messages[convo_id] = messages

    return all_convos, all_messages


# ---------------------------------------------------------------------------
# DemoClient
# ---------------------------------------------------------------------------

class DemoClient:
    """Drop-in replacement for BlueskyClient that returns mock data."""

    def __init__(self) -> None:
        did, handle, display = _DEMO_USER
        self.me: ProfileData = ProfileData(
            did=did,
            handle=handle,
            display_name=display,
            description="Software engineer. Building things for the open web. she/her",
            avatar_url="",
            followers_count=1247,
            following_count=483,
            posts_count=892,
            is_following=False,
            follow_uri=None,
        )
        self._posts = _build_posts()
        self._profiles = _build_profiles()
        self._notifications = _build_notifications(self._posts)
        self._conversations, self._messages = _build_conversations_and_messages(did)

    # -- Auth ---------------------------------------------------------------

    async def login(self, handle: str, app_password: str) -> None:
        pass

    # -- Timeline / feeds ---------------------------------------------------

    async def get_timeline(
        self, cursor: str | None = None, limit: int = 30,
    ) -> tuple[list[PostData], str | None]:
        start = int(cursor) if cursor else 0
        end = start + limit
        chunk = self._posts[start:end]
        next_cursor = str(end) if end < len(self._posts) else None
        return chunk, next_cursor

    async def get_author_feed(
        self, did: str, cursor: str | None = None, limit: int = 30,
    ) -> tuple[list[PostData], str | None]:
        user_posts = [p for p in self._posts if p.author_did == did]
        start = int(cursor) if cursor else 0
        end = start + limit
        chunk = user_posts[start:end]
        next_cursor = str(end) if end < len(user_posts) else None
        return chunk, next_cursor

    # -- Threads ------------------------------------------------------------

    async def get_post_thread(self, uri: str) -> ThreadData:
        # Find the requested post
        main = None
        for p in self._posts:
            if p.uri == uri:
                main = p
                break
        if main is None:
            main = self._posts[0]

        # Build a parent post
        p_did, p_handle, p_display = _USERS[0]
        parent = PostData(
            uri=_uri(p_did, "thread_parent"),
            cid="bafyreithreadparent",
            author_did=p_did,
            author_handle=p_handle,
            author_display_name=p_display,
            text="Interesting thread on this topic. Here are my thoughts on where things are heading.",
            created_at=_ts(24),
            like_count=34,
            repost_count=5,
            reply_count=3,
            is_liked=False,
            is_reposted=False,
            like_uri=None,
            repost_uri=None,
            reason_repost_by=None,
            reply_parent_uri=None,
            reply_parent_author=None,
            reply_root_uri=None,
            embed_type=None,
            embed_text=None,
            embed_author=None,
            has_image=False,
            has_video=False,
        )

        # Build reply posts
        replies: list[PostData] = []
        reply_defs = [
            (2, "Totally agree with this. Well said!", 12, 1, 0),
            (4, "Counter-point: I think there's more nuance here than people realize. But overall yes.", 8, 0, 1),
            (6, "Thanks for sharing this perspective. Bookmarked.", 5, 0, 0),
        ]
        for i, (u_idx, text, likes, rp, rc) in enumerate(reply_defs):
            r_did, r_handle, r_display = _USERS[u_idx]
            replies.append(PostData(
                uri=_uri(r_did, f"thread_reply{i}"),
                cid=f"bafyreithreadreply{i}",
                author_did=r_did,
                author_handle=r_handle,
                author_display_name=r_display,
                text=text,
                created_at=_ts(0.5 + i * 0.3),
                like_count=likes,
                repost_count=rp,
                reply_count=rc,
                is_liked=False,
                is_reposted=False,
                like_uri=None,
                repost_uri=None,
                reason_repost_by=None,
                reply_parent_uri=main.uri,
                reply_parent_author=main.author_handle,
                reply_root_uri=parent.uri,
                embed_type=None,
                embed_text=None,
                embed_author=None,
                has_image=False,
                has_video=False,
            ))

        return ThreadData(parents=[parent], post=main, replies=replies)

    # -- Profiles -----------------------------------------------------------

    async def get_profile(self, handle_or_did: str) -> ProfileData:
        if handle_or_did in self._profiles:
            return self._profiles[handle_or_did]
        # Lookup by handle
        for prof in self._profiles.values():
            if prof.handle == handle_or_did:
                return prof
        # Fallback to first non-demo user
        return list(self._profiles.values())[1]

    # -- Notifications ------------------------------------------------------

    async def get_notifications(
        self, cursor: str | None = None,
    ) -> tuple[list[NotificationData], str | None]:
        start = int(cursor) if cursor else 0
        end = start + 30
        chunk = self._notifications[start:end]
        next_cursor = str(end) if end < len(self._notifications) else None
        return chunk, next_cursor

    async def mark_notifications_read(self) -> None:
        pass

    # -- Actions (no-ops with fake URIs) ------------------------------------

    async def like(self, uri: str, cid: str) -> str:
        return f"at://{_DEMO_USER[0]}/app.bsky.feed.like/{uuid.uuid4().hex[:12]}"

    async def unlike(self, like_uri: str) -> None:
        pass

    async def repost(self, uri: str, cid: str) -> str:
        return f"at://{_DEMO_USER[0]}/app.bsky.feed.repost/{uuid.uuid4().hex[:12]}"

    async def unrepost(self, repost_uri: str) -> None:
        pass

    async def follow(self, did: str) -> str:
        return f"at://{_DEMO_USER[0]}/app.bsky.graph.follow/{uuid.uuid4().hex[:12]}"

    async def unfollow(self, follow_uri: str) -> None:
        pass

    async def delete_post(self, uri: str) -> None:
        pass

    async def create_post(
        self,
        text: str,
        reply_to: PostData | None = None,
        quote: PostData | None = None,
    ) -> PostData:
        new_rkey = uuid.uuid4().hex[:12]
        return PostData(
            uri=_uri(_DEMO_USER[0], new_rkey),
            cid=f"bafyrei{new_rkey}",
            author_did=self.me.did,
            author_handle=self.me.handle,
            author_display_name=self.me.display_name,
            text=text,
            created_at=datetime.now(timezone.utc).isoformat(),
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

    async def resolve_repost_uri(self, repost_uri: str) -> str | None:
        return self._posts[0].uri if self._posts else None

    # -- Direct Messages ----------------------------------------------------

    async def list_conversations(
        self, cursor: str | None = None,
    ) -> tuple[list[ConversationData], str | None]:
        start = int(cursor) if cursor else 0
        end = start + 20
        chunk = self._conversations[start:end]
        next_cursor = str(end) if end < len(self._conversations) else None
        return chunk, next_cursor

    async def get_messages(
        self, convo_id: str, cursor: str | None = None,
    ) -> tuple[list[MessageData], str | None]:
        all_msgs = self._messages.get(convo_id, [])
        # Messages stored oldest-first; API would return newest-first then reversed
        # For demo, just paginate from end
        start = int(cursor) if cursor else 0
        end = start + 50
        chunk = all_msgs[start:end]
        next_cursor = str(end) if end < len(all_msgs) else None
        return chunk, next_cursor

    async def send_dm(self, convo_id: str, text: str) -> MessageData:
        msg_id = uuid.uuid4().hex[:12]
        msg = MessageData(
            id=msg_id,
            convo_id=convo_id,
            sender_did=self.me.did,
            sender_handle=self.me.handle,
            sender_display_name=self.me.display_name,
            text=text,
            sent_at=datetime.now(timezone.utc).isoformat(),
            is_mine=True,
        )
        if convo_id in self._messages:
            self._messages[convo_id].append(msg)
        return msg

    async def mark_convo_read(self, convo_id: str, message_id: str) -> None:
        pass
