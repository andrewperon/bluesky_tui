# Bluesky TUI

A terminal UI client for [Bluesky](https://bsky.app) built with Python, [Textual](https://textual.textualize.io/), and the [AT Protocol SDK](https://atproto.blue/).

## Features

- Browse your home timeline with vim-style navigation
- Like, repost, and delete posts
- Compose new posts, replies, and quote posts
- View conversation threads
- View user profiles and follow/unfollow
- View and navigate notifications
- Feed filters: all posts, posts only (no replies/reposts), text only (no images/videos)
- Settings screen with theme switching, post density, feed defaults, and notification filters
- Multi-account support with quick switching (`a` key)
- Saved credentials with auto-login
- Persistent settings stored independently from credentials

## Requirements

- Python 3.11+
- A Bluesky account with an [app password](https://bsky.app/settings/app-passwords)

## Installation

```bash
git clone https://github.com/andrewperon/bluesky_tui
cd bluesky_tui
pip install -e .
```

## Usage

```bash
python -m bluesky_tui
```

On first launch you'll be prompted for your Bluesky handle and app password. Check "Save credentials" to auto-login on future launches. Credentials are stored in `~/.config/bluesky_tui/config.json`.

## Key Bindings

### Feed

| Key | Action |
|---|---|
| `j` / `Down` | Move cursor down |
| `k` / `Up` | Move cursor up |
| `l` | Like / unlike |
| `b` | Repost / unrepost |
| `Enter` / `t` | View thread |
| `r` | Reply to post |
| `c` | Compose new post |
| `p` | View author profile |
| `u` | View your profile |
| `d` | Delete own post |
| `n` | View notifications |
| `a` | Switch account |
| `s` | Open settings |
| `f` | Cycle feed filter (all / posts only / text only) |
| `Space` | Load more posts |
| `R` | Refresh feed |
| `q` | Quit |

### Thread

| Key | Action |
|---|---|
| `j` / `k` | Navigate posts |
| `l` | Like / unlike |
| `r` | Reply |
| `p` | View author profile |
| `Escape` / `q` | Back |

### Profile

| Key | Action |
|---|---|
| `j` / `k` | Navigate posts |
| `f` | Follow / unfollow |
| `l` | Like / unlike |
| `Enter` / `t` | View thread |
| `Space` | Load more posts |
| `Escape` / `q` | Back |

### Notifications

| Key | Action |
|---|---|
| `j` / `k` | Navigate |
| `Enter` | Open thread / profile |
| `p` | View author profile |
| `Space` | Load more |
| `Escape` / `q` | Back |

### Settings

| Key | Action |
|---|---|
| `j` / `k` | Navigate |
| `Enter` | Cycle / toggle setting |
| `y` / `n` | Confirm / cancel log out |
| `Escape` / `q` | Back |

### Compose

| Key | Action |
|---|---|
| `Escape` | Cancel |

## Project Structure

```
src/bluesky_tui/
  __main__.py            # Entry point
  app.py                 # Main Textual App
  config.py              # Credential + settings storage
  api/
    client.py            # Async wrapper around atproto
    models.py            # Data classes (PostData, ProfileData, etc.)
  screens/
    login.py             # Login screen
    feed.py              # Home timeline
    thread.py            # Conversation view
    compose.py           # New post / reply / quote (modal)
    profile.py           # User profile + posts
    notifications.py     # Notification list
    account_switcher.py  # Account switcher screen
    settings.py          # Settings screen
  widgets/
    post.py              # Single post widget
    post_list.py         # Scrollable post container
    user_header.py       # Profile header
    notification_item.py # Single notification widget
  css/
    app.tcss             # Global styles
```

## License

MIT
