import requests
import sseclient
import json

SERVER_URL = "https://your-server-url/stream"

response = requests.get(SERVER_URL, stream=True)
client = sseclient.SSEClient(response)

for event in client.events():
    if event.event == "move":
        data = json.loads(event.data)
        print("Move received:", data)

        fen = data["fen"]

        #move = calculate_move(fen)  # your engine

        send_move(move)

def get_position():
    try:
        res = requests.get(f"{SERVER_URL}/moves")
        res.raise_for_status()
        return res.json()["fen"]
    except Exception as e:
        print("Error fetching moves", e);
        return None

def send_move(move):
    try:
        res = requests.post(
            f"{SERVER_URL}/move",
            json={"move":move},
        )
        res.raise_for_status()
        print("Move sent:", move)
    except Exception as e:
        print("Error sending move:", e)