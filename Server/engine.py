import requests
import time

SERVER_URL = "https://lichessmlbot.onrender.com"

def get_position():
    try:
        res = requests.get(f"{SERVER_URL}/moves")
        res.raise_for_status()
        return res.json()["fen"]
    except Exception as e:
        print("Error fetching moves", e);
        return None
    
def calculate_move(fen):
    return "e2e4"

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
        
def main():
    while True:
        fen = get_position()
        
        if fen:
            move = calculate_move(fen)
            if move:
                send_move(move)
                
        time.sleep(2);
        
if __name__ == "__main__":
    main()