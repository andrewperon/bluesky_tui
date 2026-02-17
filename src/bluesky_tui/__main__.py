import argparse

from bluesky_tui.app import BlueskyApp


def main():
    parser = argparse.ArgumentParser(description="Bluesky TUI")
    parser.add_argument("--demo", action="store_true", help="Run with mock data for screenshots")
    args = parser.parse_args()

    client = None
    if args.demo:
        from bluesky_tui.api.demo_client import DemoClient
        client = DemoClient()

    app = BlueskyApp(client=client)
    app.run()


if __name__ == "__main__":
    main()
