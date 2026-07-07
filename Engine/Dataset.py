import chess.pgn
pgn = open("GameDatabase/lichess_db_standard_rated_2019-05.pgn")
while True:
    game = chess.pgn.read_game(pgn)
    if game is None:
        break
    print(game.headers["White"], game.headers["Black"])
    
    board = game.board()
    for move in game.mainline_moves():
        board.push(move)
        print(board)
        print("\n")