"""
Converts lichess-style FEN + Stockfish eval data (like your extracted JSONL)
into PyTorch tensors for training a value network.

Expected input: a file where each line is one JSON object like:
{"fen": "...", "evals": [{"pvs": [{"cp": 69, "line": "..."}, ...], "knodes": ..., "depth": 46}, ...]}

Usage:
    dataset = ChessEvalDataset("evals.jsonl")
    loader = DataLoader(dataset, batch_size=256, shuffle=True)
    for boards, targets in loader:
        ...
"""

import json
import torch
import numpy as np
from torch.utils.data import Dataset

# --- Board encoding ---------------------------------------------------

PIECE_TO_PLANE = {
    'P': 0, 'N': 1, 'B': 2, 'R': 3, 'Q': 4, 'K': 5,
    'p': 6, 'n': 7, 'b': 8, 'r': 9, 'q': 10, 'k': 11,
}


def fen_to_tensor(fen: str) -> torch.Tensor:
    """
    Encodes a FEN into a (18, 8, 8) tensor:
      planes 0-11:  piece placement (6 piece types x 2 colors)
      plane 12:     side to move (all 1s if white to move, else all 0s)
      planes 13-16: castling rights (K, Q, k, q) as constant planes
      plane 17:     en passant target square (1 at that square, else 0)
    """
    parts = fen.split(' ')
    board_part = parts[0]
    side_to_move = parts[1] if len(parts) > 1 else 'w'
    castling = parts[2] if len(parts) > 2 else '-'
    en_passant = parts[3] if len(parts) > 3 else '-'

    planes = np.zeros((18, 8, 8), dtype=np.float32)

    rows = board_part.split('/')
    for rank_idx, row in enumerate(rows):  # rank_idx 0 = rank 8 (top of FEN)
        file_idx = 0
        for ch in row:
            if ch.isdigit():
                file_idx += int(ch)
            else:
                plane = PIECE_TO_PLANE[ch]
                # convert FEN rank order (8->1) into array row 0=rank1 ... 7=rank8
                array_rank = 7 - rank_idx
                planes[plane, array_rank, file_idx] = 1.0
                file_idx += 1

    if side_to_move == 'w':
        planes[12, :, :] = 1.0

    if 'K' in castling:
        planes[13, :, :] = 1.0
    if 'Q' in castling:
        planes[14, :, :] = 1.0
    if 'k' in castling:
        planes[15, :, :] = 1.0
    if 'q' in castling:
        planes[16, :, :] = 1.0

    if en_passant != '-':
        file_idx = ord(en_passant[0]) - ord('a')
        rank_idx = int(en_passant[1]) - 1
        planes[17, rank_idx, file_idx] = 1.0

    return torch.from_numpy(planes)


# --- Eval / target encoding --------------------------------------------

def mate_to_cp(mate_in: int, decay: float = 100.0, base: float = 10000.0) -> float:
    """
    Converts a 'mate in N' score into a large centipawn-equivalent value.
    Sign follows the sign of mate_in (positive = side to move mates,
    negative = side to move gets mated). Decays slightly with distance
    so 'mate in 1' scores higher than 'mate in 30'.
    """
    sign = 1.0 if mate_in > 0 else -1.0
    n = abs(mate_in)
    return sign * (base - decay * min(n, 99))


def extract_target(evals: list) -> float:
    """
    Takes the 'evals' list from one JSONL record and returns a single
    scalar training target in centipawns (from the side-to-move's perspective).
    """
    # Prefer the block with the greatest search depth
    best_block = max(evals, key=lambda e: _get_depth(e))
    first_pv = best_block['pvs'][0]  # best move = first PV

    if 'mate' in first_pv:
        return mate_to_cp(first_pv['mate'])
    return float(first_pv['cp'])


def _get_depth(eval_block: dict) -> int:
    # depth is stored alongside knodes in your sample, one level inside pvs' parent
    return eval_block.get('depth', 0)


def normalize_target(cp: float, clip: float = 1000.0) -> float:
    """
    Squashes a centipawn value into roughly [-1, 1] using tanh, which is a
    common approach for value-network targets. `clip` controls how quickly
    it saturates (smaller clip = saturates sooner).
    """
    return float(np.tanh(cp / clip))
