import pygame as p
import chessEngine

p.init()

def load_images():
    pieces = ["bR", "bN", "bB", "bQ", "bK","bp","wR", "wN", "wB", "wQ", "wK","wp"]
    for piece in pieces:
        IMAGES[piece] = p.transform.scale(p.image.load("Images/"+piece+".png"),(SQ_SIZE,SQ_SIZE))

def drawboard(screen):
    colors = [p.Color((255,255,255)),p.Color((186, 140, 99))]

    for r in range(DIMENSION):
        for c in range(DIMENSION):
            color = colors[((r+c)%2)]
            p.draw.rect(screen,color,p.Rect(c*SQ_SIZE,r*SQ_SIZE,SQ_SIZE,SQ_SIZE))

def draw_pieces(screen,board):
    for r in range(DIMENSION):
        for c in range(DIMENSION):
            piece = board[r][c]
            if piece != "--":
                screen.blit(IMAGES[piece],p.Rect(c*SQ_SIZE,r*SQ_SIZE,SQ_SIZE,SQ_SIZE))

def draw_game_state(screen,gs):
    drawboard(screen)
    draw_pieces(screen, gs.board)

WIDTH = HEIGHT = 512
DIMENSION = 8
SQ_SIZE = HEIGHT // DIMENSION
MAX_FPS = 15
IMAGES = {}

p.display.set_caption("CHESS")
icon = p.image.load("Images/chess.png")
p.display.set_icon(icon)

screen = p.display.set_mode((WIDTH,HEIGHT+100))
clock = p.time.Clock()
screen.fill(p.Color("white"))
gs = chessEngine.GameState()
load_images()
running = True
sqSelected = ()
playerClicks = []

while running:

    for event in p.event.get():
        if event.type == p.QUIT:
            running = False
        elif event.type == p.MOUSEBUTTONDOWN:
            location = p.mouse.get_pos()
            col = location[0] // SQ_SIZE
            row = location[1] // SQ_SIZE
            if sqSelected == (row,col): # if same player clicked twice
                sqSelected = ()     # deselect
                playerClicks = []   # Clear the player click
            else:
                sqSelected = (row,col)
                playerClicks.append(sqSelected)
            if len(playerClicks) == 2:
                move = chessEngine.Move(playerClicks[0],playerClicks[1],gs.board)
                print(move.getChessNotation())
                gs.makeMove(move)
                sqSelected = () # reset to default
                playerClicks = [] # reset to default
            sqSelected = (row,col)
    draw_game_state(screen,gs)
    clock.tick(MAX_FPS)
    p.display.flip()
