import os
import sys
from tkinter import *
from tkinter import messagebox

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

def boardToFen(board):
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
    fen += " b"
    return fen


class NeuralNetwork():
    def __init__(self):
        self.optimizer = 'Adam'
        self.loss = 'categorical_crossentropy'

    def define(self):
        input_layer = Input(shape=(8, 8, 12))
        x = Conv2D(filters=64, kernel_size=2, strides=(2, 2))(input_layer)
        x = Conv2D(filters=128, kernel_size=2, strides=(2, 2))(x)
        x = Conv2D(filters=256, kernel_size=2, strides=(2, 2))(x)
        x = Flatten()(x)

        x = Dense(4096, activation='softmax')(x)
        output = Reshape((1, 64, 64))(x)

        model = Model(inputs=input_layer, outputs=output)
        model.compile(optimizer=self.optimzier, loss=self.loss)
        self.model = model

    def train(self, X, y, epochs, EarlyStop=True):
        if EarlyStop:
            es = EarlyStopping(monitor='loss')

        self.model.fit(X, y, epochs=epochs, callbacks=[es])
        self.model.save('chess_model')

    def predict(self, board, side):
        model = load_model("chess_model")
        translated = translate_board(board)
        move_matrix = model(translated.reshape(1, 8, 8, 12))[0][0]

        move_matrix = filter_legal_moves(board, move_matrix)
        move = np.unravel_index(np.argmax(move_matrix, axis=None), move_matrix.shape)
        move = chess.Move(move[0], move[1])
        return move, 1


def material_counter(board):
    material = np.array([0, 0])
    translated_board = board_matrix(board)
    for piece in translated_board:
        material += value_dict[piece]
    return material


def pos_cont(board):
    boards = []
    legal_moves = list(board.legal_moves)
    for move in legal_moves:
        copy_board = board.copy()
        copy_board.push(move)
        boards.append(copy_board)
    return boards, legal_moves


class Node:
    def __init__(self, board, move, parent):
        self.board = board
        self.move = move
        self.parent_node = parent
        self.child_nodes = []
        self.utility = [0, 0]
        self.func = None

    def evaluate(self, idx):
        if len(self.child_nodes) == 0:
            material = material_counter(self.board)
            white = material[0]
            black = material[1]
            if idx == 0:
                self.utility = black - white
            else:
                self.utility = white - black
        else:
            child_util = [node.utility for node in self.child_nodes]
            self.utility = self.func(child_util)

    def extend(self):
        continuations, legal_moves = pos_cont(self.board)
        for i in range(len(continuations)):
            self.child_nodes.append(Node(continuations[i], legal_moves[i], self))


class MinMaxTree():
    def __init__(self):
        pass

    def create_root_node(self, board):
        root_node = Node(board, None, None)
        self.root_node = root_node

    def construct(self, depth=2):
        nodes = []
        prev_gen = [self.root_node]

        for i in range(depth):
            new_gen = []
            for parent_node in prev_gen:
                parent_node.extend()
                new_gen.extend(parent_node.child_nodes)
            prev_gen = new_gen
            nodes.append(prev_gen)

        self.nodes = nodes
        # self.function_list = np.array([[] + [max,min] for _ in range(depth//2)]).flatten()

        function_list = []
        if depth % 2 == 0:
            funcs = [max, min]
        else:
            funcs = [min, max]
        for i in range(depth):
            func = funcs[i % 2]
            function_list.append(func)
        self.function_list = function_list

        return self.root_node

    def evaluate(self, side):
        if side == 'White':
            idx = 0
        elif side == 'Black':
            idx = 1

        for i in range(len(self.nodes) - 1, -1, -1):
            # print('Evaluating Node',i)
            # print('Number of Nodes in layer',len(self.nodes[i]))
            for node in self.nodes[i]:
                node.func = self.function_list[i]
                node.evaluate(idx)

    def predict(self, board, side, depth=3):
        func = np.argmax
        self.create_root_node(board)
        # print('Root Node Created')
        self.construct(depth=depth)
        # print('Tree Constructed')
        self.evaluate(side)
        # print('Evaluation Complete')
        utilities = [node.utility for node in self.nodes[0]]
        effe = func(utilities)
        move = self.nodes[0][func(utilities)].move
        if 'x' in board.san(move):
            effe = 1
        return move, effe


class ChessEngine():

    def __init__(self, algorithms=[MinMaxTree, NeuralNetwork]):
        self.algorithms = algorithms

    def generate_move(self, board, side):
        moves = []
        effes = []
        for algorithm in self.algorithms:
            move, effe = algorithm().predict(board, side)
            moves.append(move)
            effes.append(effe)

        effes = np.array(effes)
        idx = np.argmax(effes)

        final_move = moves[idx]
        print(self.algorithms[idx])
        print(effes)
        return final_move


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
                                    print(validMoves[i].getChessNotation())
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
                print("Random moves")
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
                                    print(validMoves[i].getChessNotation())
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
            board = chess.Board(boardToFen(gs.board))
            engine = NeuralNetwork()
            AIMove, effe = engine.predict(board, side='Black')
            print("AIMOVE : ", AIMove)
            for i in range(len(validMoves)):
                if str(validMoves[i].getChessNotation()) == str(AIMove):
                    gs.makeMove(validMoves[i])
                    moveMade = True
                    animate = True
            if moveMade == False:
                print("Random moves")
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
                                    print(validMoves[i].getChessNotation())
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
            board = chess.Board(boardToFen(gs.board))
            engine = ChessEngine(algorithms=[MinMaxTree, NeuralNetwork])
            AIMove = engine.generate_move(board, side='Black')
            print("AIMOVE : ", AIMove)
            for i in range(len(validMoves)):
                if str(validMoves[i].getChessNotation()) == str(AIMove):
                    gs.makeMove(validMoves[i])
                    moveMade = True
                    animate = True
            if moveMade == False:
                print("Random moves")
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
            else:
                draw_text(screen, "White wins by checkMate")
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
