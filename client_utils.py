"""
Helper functions shared by the client programs (send.py, receive.py, menu.py).

Putting these in one file means we write them once and every client can
reuse them.
"""

import socket

from common import HOST, PORT, receive_message, send_message

# The choices the user can pick from. Change these lists to suit your assets.
CATEGORIES = ["IT Equipment", "Furniture", "Vehicles", "Tools", "Other"]
STATUSES = ["In Use", "In Store", "Under Repair", "Retired"]


# ---------------------------------------------------------------------------
# Talking to the server
# ---------------------------------------------------------------------------

def send_request(message):
    """Send one request to the server and return its reply.

    If something goes wrong, print a simple message and return None.
    """
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)  # give up after 5 seconds instead of waiting forever
        sock.connect((HOST, PORT))
        send_message(sock, message)
        reply = receive_message(sock)
        sock.close()
        return reply
    except ConnectionRefusedError:
        print("Could not connect to the server - is server.py running?")
    except Exception as error:
        print("Something went wrong:", error)
    return None


def get_assets():
    """Ask the server for the list of assets. Returns None if it fails."""
    response = send_request({"action": "LIST"})
    if response is None:
        return None
    if response.get("status") != "OK":
        print("Server returned an error:", response.get("detail"))
        return None

    # Only keep entries that are proper records (dictionaries).
    good_assets = []
    for asset in response.get("assets", []):
        if isinstance(asset, dict):
            good_assets.append(asset)
    return good_assets


# ---------------------------------------------------------------------------
# Asking the user for input
# ---------------------------------------------------------------------------

def ask(prompt):
    """Keep asking until the user types something (not blank)."""
    while True:
        value = input(prompt).strip()
        if value != "":
            return value
        print("  This field cannot be empty. Please try again.")


def ask_asset_id():
    """Keep asking until the ID looks like AST-0001."""
    while True:
        value = input("  Asset ID (format AST-0001): ").strip().upper()
        # Must start with AST-, be 8 characters long, and end in 4 digits.
        if value.startswith("AST-") and len(value) == 8 and value[4:].isdigit():
            return value
        print("  Invalid ID. It must look like AST-0001.")


def choose(prompt, options):
    """Show a numbered list and keep asking until a valid number is picked."""
    print(prompt)
    number = 1
    for option in options:
        print(f"    {number}. {option}")
        number = number + 1

    while True:
        answer = input("  Enter a number: ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print(f"  Please enter a number between 1 and {len(options)}.")


def confirm(prompt):
    """Ask a yes/no question. Returns True for yes, False for no."""
    while True:
        answer = input(prompt + " (y/n): ").strip().lower()
        if answer == "y":
            return True
        if answer == "n":
            return False
        print("  Please type y or n.")


# ---------------------------------------------------------------------------
# Showing results
# ---------------------------------------------------------------------------

def print_assets(assets):
    """Print the assets as a table with fixed-width columns."""
    print(f"{'ID':<10}{'Description':<30}{'Category':<15}{'Location':<20}{'Status':<15}{'Registered':<12}")
    print("-" * 102)
    for asset in assets:
        print(f"{asset.get('asset_id', ''):<10}"
              f"{asset.get('description', ''):<30}"
              f"{asset.get('category', ''):<15}"
              f"{asset.get('location', ''):<20}"
              f"{asset.get('status', ''):<15}"
              f"{asset.get('date_registered', ''):<12}")
