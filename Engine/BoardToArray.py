import chess
import numpy as np

def board_to_array(board):
    piece_values = {
        chess.PAWN: 1, chess.KNIGHT: 3, chess.BISHOP: 3,
        chess.ROOK: 5, chess.QUEEN: 9, chess.KING: 100
    }

    squares = np.zeros(64, dtype=np.float32)

    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            value = piece_values[piece.piece_type]
            # white = positive, black = negative
            squares[square] = value if piece.color == chess.WHITE else -value

    # Extra context
    turn = np.array([1.0 if board.turn == chess.WHITE else -1.0])
    castling = np.array([
        float(board.has_kingside_castling_rights(chess.WHITE)),
        float(board.has_queenside_castling_rights(chess.WHITE)),
        float(board.has_kingside_castling_rights(chess.BLACK)),
        float(board.has_queenside_castling_rights(chess.BLACK)),
    ])
    en_passant = np.array([float(board.ep_square is not None)])

    return np.concatenate([squares, turn, castling, en_passant])

# Try it:
board = chess.Board()
encoded = board_to_array(board)
print(encoded.shape)   # (69,)
print(encoded[:8])     # first rank: rook, knight, bishop, queen, king, bishop, knight, rook