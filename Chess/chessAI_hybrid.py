
from keras.models import Input,Model
from keras.layers import Dense,Flatten,Reshape
from keras.layers.convolutional import Conv2D
from keras.callbacks import EarlyStopping
from keras.models import load_model
from board_conversion import *
from chessEngine import *
import chess


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
    material = np.array([0,0])
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
    return boards,legal_moves


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