"""
"Send" client (IMPROVED).

Prompts you for the details of one asset, checks them, then registers it
with the server. The server must already be running (start server.py first).

    python send.py

Improvements over the starter code:
  - empty answers are rejected and the question is asked again
  - the asset ID must match the format AST-0001
  - category and status are chosen from numbered lists (no typos)
  - the client checks the ID is not already in use before sending
  - a summary is shown and the user confirms before anything is sent
  - friendly messages replace error tracebacks
"""

import datetime

from client_utils import (
    CATEGORIES,
    STATUSES,
    ask,
    ask_asset_id,
    choose,
    confirm,
    get_assets,
    send_request,
)


def prompt_for_asset(existing_ids: set) -> dict:
    """Ask the user for each field of a new asset record."""
    print("Enter the details of the new asset:")

    # Keep asking for an ID until it is not one the server already has.
    while True:
        asset_id = ask_asset_id()
        if asset_id in existing_ids:
            print(f"  {asset_id} is already in use. Please choose a different ID.")
        else:
            break

    description = ask("  Description (e.g. Dell Latitude 5440 laptop): ")
    category = choose("  Category:", CATEGORIES)
    location = ask("  Location (e.g. Site A - IT Store): ")
    status = choose("  Status:", STATUSES)

    return {
        "asset_id": asset_id,
        "description": description,
        "category": category,
        "location": location,
        "status": status,
        "date_registered": datetime.date.today().isoformat(),
    }


def register_asset() -> None:
    """Collect an asset from the user and send it to the server."""
    # Fetch the current assets first so we can spot duplicate IDs.
    assets = get_assets()
    if assets is None:
        return  # a message has already been printed (e.g. server not running)
    existing_ids = {a.get("asset_id") for a in assets}

    new_asset = prompt_for_asset(existing_ids)

    # Show a summary and let the user back out before anything is sent.
    print("\nPlease check the details:")
    for field, value in new_asset.items():
        print(f"  {field}: {value}")
    if not confirm("\nRegister this asset?"):
        print("Cancelled - nothing was sent.")
        return

    response = send_request({"action": "REGISTER", "asset": new_asset})
    if response is None:
        return
    if response.get("status") == "OK":
        print(f"Success: asset {new_asset['asset_id']} was registered.")
    else:
        print("The server rejected the asset:", response.get("detail"))


def main() -> None:
    register_asset()


# Only run this if the file is executed directly (not imported).
if __name__ == "__main__":
    try:
        main()
        input("\nPress Enter to close...")
    except (EOFError, KeyboardInterrupt):
        # Input ended or the user pressed Ctrl+C - just exit quietly.
        print()
