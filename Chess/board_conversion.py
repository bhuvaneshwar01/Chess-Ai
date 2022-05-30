import numpy as np
chess_dict = {
    'p' : [1,0,0,0,0,0,0,0,0,0,0,0],
    'P' : [0,0,0,0,0,0,1,0,0,0,0,0],
    'n' : [0,1,0,0,0,0,0,0,0,0,0,0],
    'N' : [0,0,0,0,0,0,0,1,0,0,0,0],
    'b' : [0,0,1,0,0,0,0,0,0,0,0,0],
    'B' : [0,0,0,0,0,0,0,0,1,0,0,0],
    'r' : [0,0,0,1,0,0,0,0,0,0,0,0],
    'R' : [0,0,0,0,0,0,0,0,0,1,0,0],
    'q' : [0,0,0,0,1,0,0,0,0,0,0,0],
    'Q' : [0,0,0,0,0,0,0,0,0,0,1,0],
    'k' : [0,0,0,0,0,1,0,0,0,0,0,0],
    'K' : [0,0,0,0,0,0,0,0,0,0,0,1],
    '.' : [0,0,0,0,0,0,0,0,0,0,0,0],
}

value_dict = {
    'p': [1, 0],
    'P': [0, 1],
    'n': [3, 0],
    'N': [0, 3],
    'b': [3, 0],
    'B': [0, 3],
    'r': [5, 0],
    'R': [0, 5],
    'q': [9, 0],
    'Q': [0, 9],
    'k': [0, 0],
    'K': [0, 0],
    '.': [0, 0]
}


def translate_board(board):
    pgn = board.epd()
    foo = []
    pieces = pgn.split(" ", 1)[0]
    rows = pieces.split("/")
    for row in rows:
        foo2 = []
        for thing in row:
            if thing.isdigit():
                for i in range(0, int(thing)):
                    foo2.append(chess_dict['.'])
            else:
                foo2.append(chess_dict[thing])
        foo.append(foo2)
    return np.array(foo)

def board_matrix(board):
    pgn = board.epd()
    foo = []
    pieces = pgn.split(" ", 1)[0]
    rows = pieces.split("/")
    for row in rows:
        foo2 = []
        for thing in row:
            if thing.isdigit():
                for i in range(0, int(thing)):
                    foo.append('.')
            else:
                foo.append(thing)
    return np.array(foo)

def translate_move(move):
    from_square = move.from_square
    to_square = move.to_square
    return np.array([from_square,to_square])

def filter_legal_moves(board,logits):
    filter_mask = np.zeros(logits.shape)
    legal_moves = board.legal_moves
    for legal_move in legal_moves:
        from_square = legal_move.from_square
        to_square = legal_move.to_square
        filter_mask[from_square,to_square] = 1
    new_logits = logits*filter_mask
    return new_logits

def boardToFen(gs,board):
    a = np.char.replace(board, "bR", "r")
    a = np.char.replace(a, "bN", "n")
    a = np.char.replace(a, "bB", "b")
    a = np.char.replace(a, "bQ", "q")
    a = np.char.replace(a, "bK", "k")
    a = np.char.replace(a, "bp", "p")

    a = np.char.replace(a, "wN", "N")
    a = np.char.replace(a, "wB", "B")
    a = np.char.replace(a, "wQ", "Q")
    a = np.char.replace(a, "wK", "K")
    a = np.char.replace(a, "wp", "P")
    a = np.char.replace(a, "wR", "R")
    a = np.char.replace(a, "--", "")

    fen = ""
    RANK_SEPERATOR = "/"
    for rank in range(8):
        empty = 0
        rankFen = ""
        for file in range(8):
            if len(a[rank][file]) == 0:
                empty = empty + 1
            else:
                if empty != 0:
                    rankFen += str(empty)
                rankFen += a[rank][file]
                empty = 0
        if empty != 0:
            rankFen += str(empty)
        fen += rankFen
        if not (rank == len(board) - 1):
            fen += RANK_SEPERATOR
        else:
            fen += " "
    side = 'w' if gs.whiteToMove else 'b'
    fen += ' ' + side
    return fen