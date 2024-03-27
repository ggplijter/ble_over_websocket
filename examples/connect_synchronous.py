import websockets.exceptions
from websockets.sync.client import connect

def connect_synchronous():
    with connect("ws://localhost:8765") as websocket:
        websocket.send("disconnect")
        while True:
            try:
                message = websocket.recv()
            except websockets.exceptions.ConnectionClosedError:
                print("disconnected from server")
                break
            print(f"Received: {message}")

if __name__ == "__main__":
    connect_synchronous()