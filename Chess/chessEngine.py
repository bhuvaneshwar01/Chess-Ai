import numpy as np


class GameState():
    def __init__(self):
        self.board = np.array([
            ["bR", "bN", "bB", "bQ", "bK", "bB", "bN", "bR"],
            ["bp", "bp", "bp", "bp", "bp", "bp", "bp", "bp"],
            ["--", "--", "--", "wQ", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "--", "--", "--", "--"],
            ["--", "--", "--", "--", "bQ", "--", "--", "--"],
            ["wp", "wp", "wp", "wp", "wp", "wp", "wp", "wp"],
            ["wR", "wN", "wB", "wQ", "wK", "wB", "wN", "wR"]
        ])
        self.moveFunctions = {
            'p' : self.getPawnMoves,
            'R' : self.getRookMoves,
            'N' : self.getKnightMoves,
            'B' : self.getBishopMoves,
            'Q' : self.getQueenMoves,
            'K' : self.getKingMoves
        }
        self.whiteToMove = True
        self.moveLog = []

    def makeMove(self, move):
        self.board[move.startRow][move.startCol] = "--"
        self.board[move.endRow][move.endCol] = move.pieceMoved
        self.moveLog.append(move)  # it useful for undo moves
        self.whiteToMove = not self.whiteToMove

    def undoMove(self):
        if len(self.moveLog) != 0:
            move = self.moveLog.pop()
            self.board[move.startRow][move.startCol] = move.pieceMoved
            self.board[move.endRow][move.endCol] = move.pieceCaptured
            self.whiteToMove = not self.whiteToMove

    def getValidMoves(self):
        return self.getAllPossible()  # for now it won't check "CHECK"

    def getAllPossible(self):
        moves = []
        for r in range(len(self.board)):
            for c in range(len(self.board[r])):
                turn = self.board[r][c][0]
                if (turn == 'w' and self.whiteToMove) or (turn == 'b' and not self.whiteToMove):
                    piece = self.board[r][c][1]
                    self.moveFunctions[piece](r, c, moves)

        return moves

    def getPawnMoves(self, r, c, moves):
        if self.whiteToMove:
            if self.board[r-1][c] == "--":
                moves.append(Move((r,c),(r-1,c),self.board))
                if r == 6 and self.board[r-2][c] == "--":
                    moves.append(Move((r,c),(r-2,c),self.board))
            if c-1 >= 0:
                if self.board[r-1][c-1][0] == 'b': # Enemy piece capture
                    moves.append(Move((r,c),(r-1,c-1),self.board))
            if c+1 < 8:
                if self.board[r-1][c+1][0] == 'b': # Enemy piece capture
                    moves.append(Move((r,c),(r-1,c+1),self.board))

        else:
            if self.board[r+1][c] == "--":
                moves.append(Move((r,c),(r+1,c),self.board))
                if r == 1 and self.board[r+2][c] == "--":
                    moves.append(Move((r,c),(r+2,c),self.board))

            if c-1 >= 0:
                if self.board[r+1][c-1][0] == 'w': # Enemy piece capture
                    moves.append(Move((r,c),(r+1,c-1),self.board))

            if c+1 < 8:
                if self.board[r+1][c+1][0] == 'w': # Enemy piece capture
                    moves.append(Move((r,c),(r+1,c+1),self.board))


    def getRookMoves(self, r, c, moves):
        pass

    def getKingMoves(self, r, c, moves):
        pass

    def getQueenMoves(self, r, c, moves):
        pass

    def getBishopMoves(self, r, c, moves):
        pass

    def getKnightMoves(self, r, c, moves):
        pass

class Move():
    # map keys to values
    # key : value
    ranksToRow = {"1": 7, "2": 6, "3": 5, "4": 4,
                  "5": 3, "6": 2, "7": 1, "8": 0}
    rowsToRanks = {v: k for k, v in ranksToRow.items()}
    filesToCols = {"a": 0, "b": 1, "c": 2, "d": 3,
                   "e": 4, "f": 5, "g": 6, "h": 7}
    colsToFiles = {v: k for k, v in filesToCols.items()}

    def __init__(self, startSq, endSq, board):
        self.startRow = startSq[0]
        self.startCol = startSq[1]
        self.endRow = endSq[0]
        self.endCol = endSq[1]
        self.pieceMoved = board[self.startRow][self.startCol]
        self.pieceCaptured = board[self.endRow][self.endCol]
        self.moveID = self.startRow * 1000 + self.startCol * 100 + self.endRow * 10 + self.endCol
        print(self.moveID)

    # Overriding equal method
    def __eq__(self, other):
        if isinstance(other, Move):
            return self.moveID == other.moveID
        return False

    def getRankFiles(self, r, c):
        return self.colsToFiles[c] + self.rowsToRanks[r]

    def getChessNotation(self):
        return self.getRankFiles(self.startRow, self.startCol) + self.getRankFiles(self.endRow, self.endCol)
