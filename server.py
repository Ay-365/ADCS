"""
Asset Management System server (STARTER CODE).

Listens for one connection at a time and understands two request actions:

    {"action": "REGISTER", "asset": {...}}   -> stores the asset, replies with a status
    {"action": "LIST"}                       -> replies with every stored asset

Deliberately basic — this is a starting point, not a finished system:
  - only one client is served at a time (no threading/concurrency)
  - assets are stored in memory only and are lost when the server stops
  - there is almost no validation of incoming data
  - there is no authentication or encryption

Reviewing, extending, testing, and documenting these limitations is part
of the assignment.
"""

import socket  # provides the networking building blocks (sockets)
import json    # used to save and load assets reccords in a json file 

# Import the shared constants/helpers used by every part of the prototype.
from common import HOST, PORT, receive_message, send_message

assets = []  # in-memory "database" of registered assets (a plain list of dicts)
ASSET_FILE = "assets.json" #file to permanently store the assets

def save_assets():
    """save the assets to a json file"""

    #opens file in write mode and saves to asset list
    with open(ASSET_FILE, "w") as f:
        json.dump(assets, f, indent=4)

def load_assets():
    """ loads previously saved assest from json file """

    try:
        #opens json file and loads saved assets 
        with open(ASSET_FILE, "r") as file:
            return json.load(file)

    except FileNotFoundError:
        #if the file does not exists it returns an empty list
        return []

def validate_asset(asset):
    """ check that an asset contains all of the required info"""

    #List of fields that every asset must have 
    required_fields = [
        "asset_id",
        "description",
        "category",
        "location",
        "status",
        "date_registered"
    ]

    #make sure thit the asset recieved from the client is a dictionary
    if not isinstance(asset, dict):
        return False, "Invalid asset data" 

    #check each field exists and has a value
    for field in required_fields:

        #check that the field is actually included in the asset
        if field not in asset:
            return False, f"Missing field: {field}"

        #check that the field has not been left empty
        if not asset[field]:
            return False,f"{field} CANNOT BE EMPTY"

    #if all checks have passed , the asset is valid
    return True,""

def asset_id_exists(asset_id):
    """ this is to check if an asset with the same ID has been registered before"""

    #go thru each asset stored
    for asset in assets:

        #check if the if the ID already exists
        if asset["asset_id"] == asset_id:
            return True

    #no matching ASSET ID was found
    return False

def handle_client(conn: socket.socket) -> None:
    # `with conn:` guarantees the connection is closed automatically once
    # this block finishes, even if an error happens inside it.
    with conn:
        try:
            # Wait for, and decode, one complete message from this client.
            request = receive_message(conn)
        except (ConnectionError, ValueError) as exc:
            # ValueError covers JSON that doesn't parse; ConnectionError
            # covers a client that disconnects mid-message.
            send_message(conn, {"status": "ERROR", "detail": str(exc)})
            return  # nothing more we can do with this connection

        # Every request must say what it wants done via an "action" field.
        action = request.get("action")

        if action == "REGISTER":
            # Pull the asset details out of the request.
            asset = request.get("asset")

            #check that the asset contains all of the required information
            valid, error_message = validate_asset(asset)

            if not valid:
                send_message(
                    conn,
                    {
                        "status": "ERROR",
                        "detail": error_message
                    }
                )
                return

            #check if ID has been registered
            if asset_id_exists(asset["asset_id"]):
                send_message(
                    conn,
                    {
                        "status": "ERROR",
                        "detail": f"ASSET ID {asset['asset_id']} ALREADY EXISTS"
                    }
                )
                return

           # has passed all checks 
            assets.append(asset)  # add it to the in-memory list

            save_assets() #saves the updated asset



            # Tell the client the registration succeeded, and echo back
            # what was stored so it can be confirmed on screen.
            send_message(conn, {"status": "OK", "stored": asset})

        elif action == "LIST":
            # Send back the full current list of assets as-is.
            send_message(conn, {"status": "OK", "assets": assets})

        elif action == "UPDATE":
            #gets the updated asset info sent by client
            updated_asset= request.get("asset")

            #checks that updated asset has all required info
            valid, error_message = validate_asset(updated_asset)

            if not valid:
                send_message(
                    conn,
                    {
                        "status": "ERROR",
                        "detail": error_message
                    }
                )
                return 

            #look through the stored assets for the matching ASST ID
            for asset in assets:
                if asset["asset_id"] == updated_asset["asset_id"]:

                    #replace old info with the updated info
                    asset.update(updated_asset)

                    #save changes to assets.json
                    save_assets()

                    #tells client that update was successful
                    send_message(
                        conn,
                        {
                            "status": "OK",
                            "detail": "ASSET UPDATED SUCCESSFULLY",
                        
                        }
                    )
                    return
            #if no matching asset ID was found - sends an error
            send_message(
                conn,
                {
                    "status": "ERROR",
                    "detail": f"ASSET ID {updated_asset['asset_id']} NOT FOUND"
                }
            )


        elif action == "DELETE":
            #get the Asset ID that the client wants to delete
            asset_id = request.get("asset_id")

            #checks that asset id was actually provided
            if not asset_id:
                send_message(
                    conn,
                    {
                        "status": "ERROR",
                        "detail": "ASSET ID IS REQUIRED"
                    }
                )
                return

            #Looks thru the stored assets for matching ID
            for asset in assets:
                if asset["asset_id"] == asset_id:

                    #removes the asset from the list
                    assets.remove(asset)

                    #save changes to assets.json
                    save_assets()

                    #tells client that deletion was successful
                    send_message(
                        conn,
                        {
                            "status": "OK",
                            "detail": "DELETION SUCCESSFUL"
                        }
                    )
                    return

                #If no match is found - sends and error
            send_message(
                conn,
                {
                    "status": "ERROR",
                    "detail": f"ASSET ID {asset_id} NOT FOUND"
                }
            )


        else:
            # Any action we don't recognise is treated as an error.
            send_message(conn, {"status": "ERROR", "detail": f"Unknown action: {action!r}"})


def main() -> None:
    global assets

    #loads previously saved assets when server starts
    assets = load_assets()

    # Create a TCP/IPv4 socket. `with` closes it automatically on exit.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_sock:
        # Allow the port to be reused immediately after the server stops,
        # instead of Windows/Linux holding on to it for a short while.
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        # Bind the socket to our chosen host/port, then start listening
        # for incoming connections (this does not accept any yet).
        server_sock.bind((HOST, PORT))
        server_sock.listen()

        print(f"Asset Management server listening on {HOST}:{PORT}")
        print("Press Ctrl+C to stop.")

        # Serve clients forever, one at a time, until the server is stopped.
        while True:
            # Block here until a client connects; `conn` is a new socket
            # dedicated to that one client, `addr` is their address.
            conn, addr = server_sock.accept()
            print(f"Connection from {addr}")

            # Handle this client's single request/response fully before
            # looping back round to accept() the next one.
            handle_client(conn)


# Only run main() if this file is executed directly (not imported).
if __name__ == "__main__":
    main()
