import os
import time
import json
import random
import logging
import requests
import sseclient
import chess

# Simple starter engine that listens to the Node server SSE and posts moves.
# Env:
#  - SERVER_BASE: base URL of your Node middleman (default http://localhost:3000)
#  - API_POST_KEY: API key sent in header "x-post-key" to authorize POST /move
SERVER_BASE = os.environ.get("SERVER_BASE", "https://lichessmlbot.onrender.com")
STREAM_URL = f"{SERVER_BASE}/stream"   # SSE endpoint served by Server/Server.js
MOVE_URL = f"{SERVER_BASE}/move"       # POST endpoint served by Server/Server.js
API_POST_KEY = os.environ.get("API_POST_KEY")

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def build_board_from_moves(moves):
    """
    Build a python-chess Board from an ordered list of moves.

    - Accepts moves as UCI (e2e4) or SAN (Nf3) where possible.
    - If a move fails to parse, it is skipped (prevents crashing on malformed input).
    - Returns a chess.Board representing the position after applying moves.
    """
    board = chess.Board()
    for m in moves:
        if not m:
            continue
        # Try UCI first (most of our code uses uci). If that fails, try SAN.
        try:
            board.push_uci(m)
        except Exception:
            try:
                board.push_san(m)
            except Exception:
                # Skip any unparseable move (this keeps the engine robust to bad input)
                pass
    return board


def choose_move(board):
    """
    Choose a move given a python-chess Board.

    Current placeholder strategy:
      - Pick a uniformly random legal move.
    Important details:
      - Returns the move in UCI string form (e.g. "e2e4") so the server can post it.
      - If no legal moves (game over, resignation, checkmate), returns None.
    Replace this function with ML model inference later.
    """
    legal = list(board.legal_moves)
    if not legal:
        return None
    # chess.Move objects have .uci(); convert chosen move to UCI string expected by Lichess API
    return random.choice(legal).uci()


def send_move(move):
    """
    Send the chosen move to the Node server.

    - Adds header "x-post-key" if API_POST_KEY is configured (matches Server/Server.js auth).
    - Posts JSON {"move": move} to MOVE_URL.
    - Returns True on success, False on failure (and logs the error).
    """
    if not move:
        logging.info("No move to send")
        return False
    headers = {"x-post-key": API_POST_KEY} if API_POST_KEY else {}
    try:
        res = requests.post(MOVE_URL, json={"move": move}, headers=headers, timeout=15)
        res.raise_for_status()
        logging.info("Sent move: %s  status=%s", move, res.status_code)
        return True
    except Exception as e:
        # Log the exception but don't crash the whole engine loop
        logging.error("Error sending move: %s", e)
        return False


def run_event_loop():
    """
    Main loop: connect to the server SSE and handle incoming events.

    Behavior:
      - Connects to STREAM_URL (Server/Server.js exposes /stream which proxies `gameEvents`).
      - Uses sseclient to iterate events; each event.data is expected to be JSON with a "moves" array.
      - For each relevant event: build board -> choose move -> send move.
      - Small sleep to avoid hot-looping and to give the server time to process.
    Notes:
      - The Node server emits events via [`gameEvents`](Server/LichessStream.js).
      - The SSE event name may vary; we focus on parsing JSON payloads and the "moves" field.
      - Any malformed events are ignored to keep the engine running.
    """
    logging.info("Connecting to SSE %s", STREAM_URL)
    # Keep the request simple; sseclient wraps the streaming response for iteration
    resp = requests.get(STREAM_URL, stream=True, timeout=(10, None))
    client = sseclient.SSEClient(resp)
    for event in client.events():
        # Some servers send event.event == "message" or custom names like "move".
        # We attempt to parse any event data payload as JSON and look for "moves".
        try:
            data = json.loads(event.data)
        except Exception:
            # If parsing fails, skip this event (not necessarily fatal)
            continue

        logging.info("Event received: %s", data)
        # Expecting moves as an array; if None/empty, skip (game may have just started)
        moves = data.get("moves", []) or []
        if not moves:
            # No moves yet (or server sent a different event), nothing to do
            continue

        # Build board from move list and choose/send a move
        board = build_board_from_moves(moves)
        move = choose_move(board)
        if move:
            send_move(move)

        # Small backoff to avoid spamming POSTs and to be polite to the server
        time.sleep(0.05)


if __name__ == "__main__":
    try:
        run_event_loop()
    except KeyboardInterrupt:
        logging.info("Engine stopped by user")
    except Exception as e:
        # Catch-all to ensure crashes are logged for debugging
        logging.exception("Engine crashed: %s", e)