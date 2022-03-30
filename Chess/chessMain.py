import sys

import pygame as p

import chessEngine

p.init()

clock = p.time.Clock()
WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
IMAGES = {}

p.display.set_caption("CHESS")
icon = p.image.load("Images/chess.png")

p.display.set_icon(icon)
bg = p.transform.scale(p.image.load("Images/background.jpg"), (WIDTH + 200, HEIGHT))
screen = p.display.set_mode((WIDTH + 200, HEIGHT))

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
    colors = [p.Color((92, 64, 51)), p.Color((186, 140, 99))]

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


def draw_game_state(screen, gs):
    drawboard(screen)
    draw_pieces(screen, gs.board)


def sgame():
    running = True
    screen.fill(p.Color("white"))
    gs = chessEngine.GameState()
    validMoves = gs.getValidMoves()
    moveMade = False  # flag variable for when a move is made
    load_images()
    sqSelected = ()
    playerClicks = []
    while running:

        for event in p.event.get():
            if event.type == p.QUIT:
                p.quit()
                sys.exit()
            elif event.type == p.MOUSEBUTTONDOWN:
                location = p.mouse.get_pos()
                col = location[0] // SQ_SIZE
                row = location[1] // SQ_SIZE
                if sqSelected == (row, col):  # if same player clicked twice
                    sqSelected = ()  # deselect
                    playerClicks = []  # Clear the player click
                else:
                    sqSelected = (row, col)
                    playerClicks.append(sqSelected)
                if len(playerClicks) == 2:
                    move = chessEngine.Move(playerClicks[0], playerClicks[1], gs.board)
                    print(move.getChessNotation())
                    for i in range(len(validMoves)):
                        if move == validMoves[i]:
                            gs.makeMove(validMoves[i])
                            moveMade = True
                            sqSelected = ()  # reset to default
                            playerClicks = []  # reset to default
                    if not moveMade:
                        playerClicks = [sqSelected]

            elif event.type == p.KEYDOWN:
                if event.key == p.K_z:
                    gs.undoMove()
                    moveMade = True
                elif event.key == p.K_ESCAPE:
                    running = False
                    main_menu()

        if moveMade:
            validMoves = gs.getValidMoves()
            moveMade = False

        draw_game_state(screen, gs)
        clock.tick(15)

        p.display.flip()


def mgame():
    pass


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
