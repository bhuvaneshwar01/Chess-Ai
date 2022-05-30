from chessAI_alpha_beta import *
from chessAI_nn import *
from chessEngine import *
from board_conversion import *

import numpy as np

pieceScore = {"K": 0, "Q": 9, "R": 5, "N": 3, "B": 3, "p": 1}

knight_score = np.array([
    [0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0],
    [0.1, 0.3, 0.5, 0.5, 0.5, 0.5, 0.3, 0.1],
    [0.2, 0.5, 0.6, 0.65, 0.65, 0.6, 0.5, 0.2],
    [0.2, 0.55, 0.65, 0.7, 0.7, 0.65, 0.55, 0.2],
    [0.2, 0.5, 0.65, 0.7, 0.7, 0.65, 0.5, 0.2],
    [0.2, 0.55, 0.6, 0.65, 0.65, 0.6, 0.55, 0.2],
    [0.1, 0.3, 0.5, 0.55, 0.55, 0.5, 0.3, 0.1],
    [0.0, 0.1, 0.2, 0.2, 0.2, 0.2, 0.1, 0.0]
])

bishop_score = np.array([
    [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0],
    [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
    [0.2, 0.4, 0.5, 0.6, 0.6, 0.5, 0.4, 0.2],
    [0.2, 0.5, 0.5, 0.6, 0.6, 0.5, 0.5, 0.2],
    [0.2, 0.4, 0.6, 0.6, 0.6, 0.6, 0.4, 0.2],
    [0.2, 0.6, 0.6, 0.6, 0.6, 0.6, 0.6, 0.2],
    [0.2, 0.5, 0.4, 0.4, 0.4, 0.4, 0.5, 0.2],
    [0.0, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.0]
])

rook_score = np.array([
    [0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25],
    [0.5, 0.75, 0.75, 0.75, 0.75, 0.75, 0.75, 0.5],
    [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
    [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
    [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
    [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
    [0.0, 0.25, 0.25, 0.25, 0.25, 0.25, 0.25, 0.0],
    [0.25, 0.25, 0.25, 0.5, 0.5, 0.25, 0.25, 0.25]
])

queen_score = np.array([
    [0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0],
    [0.2, 0.4, 0.4, 0.4, 0.4, 0.4, 0.4, 0.2],
    [0.2, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
    [0.3, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
    [0.4, 0.4, 0.5, 0.5, 0.5, 0.5, 0.4, 0.3],
    [0.2, 0.5, 0.5, 0.5, 0.5, 0.5, 0.4, 0.2],
    [0.2, 0.4, 0.5, 0.4, 0.4, 0.4, 0.4, 0.2],
    [0.0, 0.2, 0.2, 0.3, 0.3, 0.2, 0.2, 0.0]
])

pawn_score = np.array([
    [0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8, 0.8],
    [0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7],
    [0.3, 0.3, 0.4, 0.5, 0.5, 0.4, 0.3, 0.3],
    [0.25, 0.25, 0.3, 0.45, 0.45, 0.3, 0.25, 0.25],
    [0.2, 0.2, 0.2, 0.4, 0.4, 0.2, 0.2, 0.2],
    [0.25, 0.15, 0.1, 0.2, 0.2, 0.1, 0.15, 0.25],
    [0.25, 0.3, 0.3, 0.0, 0.0, 0.3, 0.3, 0.25],
    [0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2]
])

piece_position_scores = {
    "wN": knight_score,
    "bN": knight_score[::-1],
    "wB": bishop_score,
    "bB": bishop_score[::-1],
    "wQ": queen_score,
    "bQ": queen_score[::-1],
    "wR": rook_score,
    "bR": rook_score[::-1],
    "wp": pawn_score,
    "bp": pawn_score[::-1],
}

CHECKMATE = 1000
STALEMATE = 0
DEPTH = 1

def scoreMaterial(game_state):
    if game_state.checkMate:
        if game_state.whiteToMove:
            return -CHECKMATE  # black win
        else:
            return CHECKMATE  # white win
    elif game_state.staleMate:
        return STALEMATE
    score = 0
    for r in range(len(game_state.board)):
        for c in range(len(game_state.board[r])):
            piece = game_state.board[r][c]
            if piece != "--":
                piece_position_score = 0
                if piece[1] != "K":
                    piece_position_score = piece_position_scores[piece][r][c]
                if piece[0] == "w":
                    score += pieceScore[piece[1]] + piece_position_score
                if piece[0] == "b":
                    score -= pieceScore[piece[1]] + piece_position_score
    return score

def findAlphaBeta(gs, valid_moves, depth, alpha, beta, turn_multiplayer):
    global bestMove
    side = 'White' if gs.whiteToMove else 'Black'
    if depth == 0:
        board = chess.Board(boardToFen(gs, gs.board))
        engine = NeuralNetwork()
        flag = False
        move =  engine.predict(board,side)
        for i in range(len(valid_moves)):
            if str(valid_moves[i].getChessNotation()) == str(move):
                gs.makeMove(valid_moves[i])
                flag = True
                break

        t = turn_multiplayer * scoreMaterial(gs)
        if flag:
            gs.undoMove()
        return t

    max_score = -CHECKMATE
    for move in valid_moves:
        gs.makeMove(move)
        bestMoves = gs.getValidMoves()
        score = -findAlphaBeta(gs, bestMoves, depth - 1, -beta, -alpha, -turn_multiplayer)
        if score > max_score:
            max_score = score
            if depth == DEPTH:
                bestMove = move
        gs.undoMove()
        if max_score > alpha:
            alpha = max_score
        if alpha >= beta:
            break
    return max_score


def findBestMoves(gs, validmoves):
    global bestMove
    bestMove = None
    random.shuffle(validmoves)
    s = findAlphaBeta(gs, validmoves, DEPTH, -CHECKMATE, CHECKMATE, 1 if gs.whiteToMove else -1)
#    print(bestMove.moveID)
    return bestMove