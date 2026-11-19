"""
"Receive" client (IMPROVED).

Asks the server for the current list of registered assets and prints
them as a neat table. The server must already be running.

    python receive.py
"""

from client_utils import get_assets, print_assets


def list_assets() -> None:
    """Fetch every asset from the server and display it."""
    assets = get_assets()
    if assets is None:
        return  # a message has already been printed

    if not assets:
        print("No assets registered yet.")
        return

    print(f"{len(assets)} asset(s) registered:\n")
    print_assets(assets)


def main() -> None:
    list_assets()


# Only run this if the file is executed directly (not imported).
if __name__ == "__main__":
    try:
        main()
        input("\nPress Enter to close...")
    except (EOFError, KeyboardInterrupt):
        print()
