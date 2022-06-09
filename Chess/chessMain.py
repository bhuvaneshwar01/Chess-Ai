import os
import sys
from tkinter import *
from tkinter import messagebox
import warnings
warnings.filterwarnings("ignore")
import chess
import pygame as p
from keras.callbacks import EarlyStopping
from keras.layers import Dense, Flatten, Reshape
from keras.layers.convolutional import Conv2D
from keras.models import Input, Model
from keras.models import load_model

import chessAI_alpha_beta
import chessEngine
from board_conversion import *
from chessEngine import *
from chessAI_hybrid import *
from score import EloRating
p.init()

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
clock = p.time.Clock()
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
IMAGES = {}

p.display.set_caption("CHESS")
icon = p.image.load("Images/chess.png")

p.display.set_icon(icon)
bg = p.transform.scale(p.image.load("Images/background.jpg"), (WIDTH + 250, HEIGHT))
screen = p.display.set_mode((WIDTH + 250, HEIGHT))

screen.fill(p.Color("white"))
gs = chessEngine.GameState()
validMoves = gs.getValidMoves()
moveMade = False  # flag variable for when a move is made
sqSelected = ()
playerClicks = []

RatingA = 1000
RatingB = 1000

def load_images():
    pieces = ["bR", "bN", "bB", "bQ", "bK", "bp", "wR", "wN", "wB", "wQ", "wK", "wp"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("Images/" + piece + ".png"), (SQ_SIZE, SQ_SIZE))


def drawboard(screen):
    global colors
    colors = [ p.Color((186, 140, 99)),p.Color((92, 64, 51))]

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r + c) % 2)]
            p.draw.rect(screen, color, p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def draw_pieces(screen, board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))


def highlightsquares(screen, gs, valid_moves, sq_selected):
    if sq_selected != ():
        r, c = sq_selected
        if gs.board[r][c][0] == ('w' if gs.whiteToMove else 'b'):
            s = p.Surface((SQ_SIZE, SQ_SIZE))
            s.set_alpha(100)
            s.fill(p.Color('blue'))
            screen.blit(s, (c * SQ_SIZE, r * SQ_SIZE))
            s.fill(p.Color('yellow'))
            for move in valid_moves:
                if move.startCol == c and move.startRow == r:
                    screen.blit(s, (move.endCol * SQ_SIZE, move.endRow * SQ_SIZE))


def draw_game_state(screen, gs, validMoves, sqSelected):
    drawboard(screen)
    highlightsquares(screen, gs, validMoves, sqSelected)
    draw_pieces(screen, gs.board)


def animate_moves(move, screen, board, clock):
    global colors
    # coords = [] #list of coords that the animation will move through
    dR = move.endRow - move.startRow
    dC = move.endCol - move.startCol
    fps = 10
    frame_count = (abs(dR) + abs(dC)) * fps
    for frame in range(frame_count + 1):
        r, c = (move.startRow + dR * frame / frame_count, move.startCol+ dC * frame / frame_count)
        drawboard(screen)
        draw_pieces(screen, board)
        color = colors[(move.endRow + move.endCol) % 2]
        endsquare = p.Rect(move.endCol * SQ_SIZE, move.endRow * SQ_SIZE, SQ_SIZE, SQ_SIZE)
        p.draw.rect(screen, color, endsquare)
        if move.pieceCaptured != '--':
            screen.blit(IMAGES[move.pieceCaptured], endsquare)
        screen.blit(IMAGES[move.pieceMoved], p.Rect(c * SQ_SIZE, r * SQ_SIZE, SQ_SIZE, SQ_SIZE))
        p.display.flip()
        clock.tick(60)


def algo_text():
    font = p.font.Font('freesansbold.ttf', 16)
    s_player = font.render(" VS ALPHA BETA PRUNING - Press '1' Key", True, (255, 255, 255))
    m_player = font.render(" VS NEURAL NETWORK - Press '2' Key", True, (255, 255, 255))
    h_player = font.render(" VS HYBRID ALGORITHM - Press '3' Key", True, (255, 255, 255))
    back = font.render(" BACK - Press '4' Key", True, (255, 255, 255))
    screen.blit(s_player, (20, 100))
    screen.blit(m_player, (20, 130))
    screen.blit(h_player, (20, 160))
    screen.blit(back, (20, 190))


def draw_text(screen, text):
    font = p.font.Font('freesansbold.ttf', 32)
    text = font.render(text, True, (255, 255, 255))
    location = p.Rect(0, 0, WIDTH, HEIGHT).move(WIDTH / 2 - text.get_width() / 2, HEIGHT / 2 - text.get_height() / 2)
    screen.blit(text, location)


def active_player(whiteToMove, score):
    font = p.font.Font(p.font.get_default_font(), 32)
    font1 = p.font.Font(p.font.get_default_font(), 16)
    if whiteToMove:
        w = font.render(" WHITE", True, (8, 143, 143))
        b = font.render(" BLACK", True, (255, 255, 255))
        screen.blit(w, (530, 30))
        screen.blit(b, (530, 60))
    else:
        w = font.render(" WHITE", True, (255, 255, 255))
        b = font.render(" BLACK", True, (8, 143, 143))
        screen.blit(w, (530, 30))
        screen.blit(b, (530, 60))
    z = font1.render("[Z]      - Undo Moves", True, (255, 255, 255))
    r = font1.render("[R]      - Redo Moves", True, (255, 255, 255))
    e = font1.render("[Esc]    - To Main Menu", True, (255, 255, 255))
    s = font.render("Score : " + str(round(score, 1)), True, (255, 255, 255), (101, 33, 33))
    screen.blit(r, (530, 160))
    screen.blit(z, (530, 210))
    screen.blit(e, (530, 270))
    score_rect = s.get_rect(center=(WIDTH + 100,HEIGHT - 100))
    screen.blit(s, score_rect)

def aivsai():
    run = True
    screen.fill((101, 33, 33))
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    animate = False
    moveMade = False  # flag variable for when a move is made
    load_images()
    sqSelected = ()
    playerClicks = []
    game_over = False
    playerOne = False # if a human is playing white then true, otherwise False for AI
    playerTwo = False

    while run:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()

            elif event.type == p.KEYDOWN:
                if event.key == p.K_r:
                    gs = chessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

                if event.key == p.K_ESCAPE:
                    run = False
                    main_menu()

        # AI move finder
        if not game_over and gs.whiteToMove:
            AIMove = chessAI_alpha_beta.findBestMoves(gs, validMoves)
            # print("AlphaBeta moves")
            if AIMove == None:
                # print("Random moves")
                AIMove = chessAI_alpha_beta.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = True
        elif not game_over:
            AIMove = findBestMoves(gs, validMoves)
            # print("AIMOVE : ", AIMove)
            for i in range(len(validMoves)):
                if str(validMoves[i].getChessNotation()) == str(AIMove.getChessNotation()):
                    gs.makeMove(validMoves[i])
                    moveMade = True
                    animate = True
                    break
            if moveMade == False:
                # print("Random moves")
                AIMove = chessAI_alpha_beta.findBestMoves(gs, validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
                if AIMove == None:
                    AIMove = chessAI_alpha_beta.findRandomMove(validMoves)
                    gs.makeMove(AIMove)
                    moveMade = True
                    animate = True

        if moveMade:
            if animate:
                animate_moves(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
        score = chessAI_alpha_beta.scoreMaterial(gs)
        draw_game_state(screen, gs, validMoves, sqSelected)

        active_player(gs.whiteToMove, score)

        if gs.checkMate:
            game_over = True
            if gs.whiteToMove:
                draw_text(screen, "Black wins by checkMate")
            else:
                draw_text(screen, "White wins by checkMate")
        elif gs.staleMate:
            draw_text(screen, "Stalemate")

        clock.tick(15)

        p.display.flip()

def alpha_beta():
    run = True
    screen.fill((101, 33, 33))
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    animate = False
    moveMade = False  # flag variable for when a move is made
    load_images()
    sqSelected = ()
    playerClicks = []
    game_over = False
    playerOne = True  # if a human is playing white then true, otherwise False for AI
    playerTwo = False

    while run:

        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                if not game_over and humanTurn:
                    location = p.mouse.get_pos()
                    if location[0] >= 0 and location[0] < 512 and location[1] >= 0 and location[1] < 512:
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        if sqSelected == (row, col):  # if same place clicked twice
                            sqSelected = ()  # deselect
                            playerClicks = []  # Clear the player click
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)
                        if len(playerClicks) == 2:
                            move = chessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    # print(validMoves[i].getChessNotation())
                                    moveMade = True
                                    animate = True
                                    sqSelected = ()  # reset to default
                                    playerClicks = []  # reset to default
                            if not moveMade:
                                playerClicks = [sqSelected]
                    else:
                        Tk().wm_withdraw()
                        messagebox.showinfo("Alert","Click within chessboard!")

            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False

                if event.key == p.K_r:
                    gs = chessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

                if event.key == p.K_ESCAPE:
                    run = False
                    main_menu()

        # AI move finder
        if not game_over and not humanTurn:
            AIMove = chessAI_alpha_beta.findBestMoves(gs, validMoves)
            if AIMove == None:
                # print("Random moves")
                AIMove = chessAI_alpha_beta.findRandomMove(validMoves)
            gs.makeMove(AIMove)
            moveMade = True
            animate = True

        if moveMade:
            if animate:
                animate_moves(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
        score = chessAI_alpha_beta.scoreMaterial(gs)
        draw_game_state(screen, gs, validMoves, sqSelected)

        active_player(gs.whiteToMove, score)

        if gs.checkMate:
            game_over = True
            if gs.whiteToMove:
                draw_text(screen, "Black wins by checkMate")
            else:
                draw_text(screen, "White wins by checkMate")
        elif gs.staleMate:
            draw_text(screen, "Stalemate")

        clock.tick(15)

        p.display.flip()


def neural_network():
    run = True
    screen.fill((101, 33, 33))
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    animate = False
    moveMade = False  # flag variable for when a move is made
    load_images()
    sqSelected = ()
    playerClicks = []
    game_over = False
    playerOne = True  # if a human is playing white then true, otherwise False for AI
    playerTwo = False

    while run:

        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                if not game_over and humanTurn:
                    location = p.mouse.get_pos()
                    if location[0] >= 0 and location[0] < 512 and location[1] >= 0 and location[1] < 512:
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        if sqSelected == (row, col):  # if same place clicked twice
                            sqSelected = ()  # deselect
                            playerClicks = []  # Clear the player click
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)
                        if len(playerClicks) == 2:
                            move = chessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    # print(validMoves[i].getChessNotation())
                                    moveMade = True
                                    animate = True
                                    sqSelected = ()  # reset to default
                                    playerClicks = []  # reset to default
                            if not moveMade:
                                playerClicks = [sqSelected]
                    else:
                        Tk().wm_withdraw()
                        messagebox.showinfo("Alert", "Click within chessboard!")

            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False

                if event.key == p.K_r:
                    gs = chessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

                if event.key == p.K_ESCAPE:
                    run = False
                    main_menu()

        # AI move finder
        if not game_over and not humanTurn:
            board = chess.Board(boardToFen(gs,gs.board))
            engine = NeuralNetwork()
            AIMove, effe = engine.predict(board, side='Black')
            # print("AIMOVE : ", AIMove)
            for i in range(len(validMoves)):
                if str(validMoves[i].getChessNotation()) == str(AIMove):
                    gs.makeMove(validMoves[i])
                    moveMade = True
                    animate = True
            if moveMade == False:
                # print("Random moves")
                AIMove = chessAI_alpha_beta.findAlphaBeta(validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
                if AIMove == None:
                    AIMove = chessAI_alpha_beta.findRandomMove(validMoves)
                    gs.makeMove(AIMove)
                    moveMade = True
                    animate = True

        if moveMade:
            if animate:
                animate_moves(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
        score = chessAI_alpha_beta.scoreMaterial(gs)
        draw_game_state(screen, gs, validMoves, sqSelected)

        active_player(gs.whiteToMove, score)

        if gs.checkMate:
            game_over = True
            if gs.whiteToMove:
                draw_text(screen, "Black wins by checkMate")
            else:
                draw_text(screen, "White wins by checkMate")
        elif gs.staleMate:
            draw_text(screen, "Stalemate")

        clock.tick(15)

        p.display.flip()


def hybrid_algorithm():
    run = True
    screen.fill((101, 33, 33))
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    animate = False
    moveMade = False  # flag variable for when a move is made
    load_images()
    sqSelected = ()
    playerClicks = []
    game_over = False
    playerOne = True  # if a human is playing white then true, otherwise False for AI
    playerTwo = False

    while run:

        humanTurn = (gs.whiteToMove and playerOne) or (not gs.whiteToMove and playerTwo)

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                if not game_over and humanTurn:
                    location = p.mouse.get_pos()
                    if location[0] >= 0 and location[0] < 512 and location[1] >= 0 and location[1] < 512:
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        if sqSelected == (row, col):  # if same place clicked twice
                            sqSelected = ()  # deselect
                            playerClicks = []  # Clear the player click
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)
                        if len(playerClicks) == 2:
                            move = chessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    # print(validMoves[i].getChessNotation())
                                    moveMade = True
                                    animate = True
                                    sqSelected = ()  # reset to default
                                    playerClicks = []  # reset to default
                            if not moveMade:
                                playerClicks = [sqSelected]
                    else:
                        Tk().wm_withdraw()
                        messagebox.showinfo("Alert", "Click within chessboard!")

            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False

                if event.key == p.K_r:
                    gs = chessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

                if event.key == p.K_ESCAPE:
                    run = False
                    main_menu()

        # AI move finder
        if not game_over and not humanTurn:
            AIMove = findBestMoves(gs,validMoves)
            # print("AIMOVE : ", AIMove)
            for i in range(len(validMoves)):
                if str(validMoves[i].getChessNotation()) == str(AIMove.getChessNotation()):
                    gs.makeMove(validMoves[i])
                    moveMade = True
                    animate = True
                    break
            if moveMade == False:
                # print("Random moves")
                AIMove = chessAI_alpha_beta.findBestMoves(gs, validMoves)
                gs.makeMove(AIMove)
                moveMade = True
                animate = True
                if AIMove == None:
                    AIMove = chessAI_alpha_beta.findRandomMove(validMoves)
                    gs.makeMove(AIMove)
                    moveMade = True
                    animate = True

        if moveMade:
            if animate:
                animate_moves(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False
        score = chessAI_alpha_beta.scoreMaterial(gs)
        draw_game_state(screen, gs, validMoves, sqSelected)

        active_player(gs.whiteToMove, score)

        if gs.checkMate:
            game_over = True
            if gs.whiteToMove:
                draw_text(screen, "Black wins by checkMate")
            else:
                draw_text(screen, "White wins by checkMate")
        elif gs.staleMate:
            draw_text(screen, "Stalemate")

        clock.tick(15)

        p.display.flip()

def sgame():
    screen.fill((0, 0, 0))
    screen.blit(bg, (0, 0))
    while True:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()

            elif event.type == p.KEYDOWN:
                if event.key == p.K_KP1:
                    alpha_beta()
                if event.key == p.K_KP2:
                    neural_network()
                if event.key == p.K_KP3:
                    hybrid_algorithm()
                if event.key == p.K_KP4:
                    main_menu()

        algo_text()
        clock.tick(15)
        p.display.flip()


def mgame():
    running = True
    screen.fill((101, 33, 33))
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    animate = False
    moveMade = False  # flag variable for when a move is made
    load_images()
    sqSelected = ()
    playerClicks = []
    game_over = False
    Ra = int(input("Enter Rating A : "))
    Rb = int(input("Enter Rating b : "))
    K = 100
    while running:

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                if not game_over:
                    location = p.mouse.get_pos()
                    if location[0] >= 0 and location[0] < 512 and location[1] >= 0 and location[1] < 512:
                        col = location[0] // SQ_SIZE
                        row = location[1] // SQ_SIZE
                        if sqSelected == (row, col):  # if same place clicked twice
                            sqSelected = ()  # deselect
                            playerClicks = []  # Clear the player click
                        else:
                            sqSelected = (row, col)
                            playerClicks.append(sqSelected)
                        if len(playerClicks) == 2:
                            move = chessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                            for i in range(len(validMoves)):
                                if move == validMoves[i]:
                                    gs.makeMove(validMoves[i])
                                    moveMade = True
                                    animate = True
                                    sqSelected = ()  # reset to default
                                    playerClicks = []  # reset to default
                            if not moveMade:
                                playerClicks = [sqSelected]
                    else:
                        Tk().wm_withdraw()
                        messagebox.showinfo("Alert","Click within chessboard!")

            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                    animate = False

                if event.key == p.K_r:
                    gs = chessEngine.GameState()
                    validMoves = gs.getValidMoves()
                    sqSelected = ()
                    playerClicks = []
                    moveMade = False
                    animate = False

                if event.key == p.K_ESCAPE:
                    running = False
                    main_menu()

        if moveMade:
            if animate:
                animate_moves(gs.moveLog[-1], screen, gs.board, clock)
            validMoves = gs.getValidMoves()
            moveMade = False
            animate = False

        draw_game_state(screen, gs, validMoves, sqSelected)
        score = chessAI_alpha_beta.scoreMaterial(gs)
        active_player(gs.whiteToMove, score)

        if gs.checkMate:
            game_over = True
            if gs.whiteToMove:
                draw_text(screen, "Black wins by checkMate")
                d = 0
                EloRating(Ra, Rb, 100, 0)
            else:
                draw_text(screen, "White wins by checkMate")
                d = 0
                EloRating(Ra, Rb, 100, 1)
        elif gs.staleMate:
            draw_text(screen, "Stalemate")

        clock.tick(15)

        p.display.flip()


def text():
    font = p.font.Font('freesansbold.ttf', 16)
    s_player = font.render(" HUMAN VS COMPUTER - Press '1' Key", True, (255, 255, 255))
    m_player = font.render(" HUMAN VS HUMAN - Press '2' Key", True, (255, 255, 255))
    screen.blit(s_player, (20, 100))
    screen.blit(m_player, (20, 130))


def main_menu():
    screen.fill((0, 0, 0))
    screen.blit(bg, (0, 0))
    while True:
        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()

            elif event.type == p.KEYDOWN:
                if event.key == p.K_KP1:
                    sgame()
                if event.key == p.K_KP2:
                    mgame()

        text()
        clock.tick(15)
        p.display.flip()


load_images()
main_menu()
# aivsai()