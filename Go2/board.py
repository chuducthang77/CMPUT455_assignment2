"""
board.py

Implements a basic Go board with functions to:
- initialize to a given board size
- check if a move is legal
- play a move

The board uses a 1-dimensional representation with padding
"""

import numpy as np
from typing import List, Tuple

from board_base import (
    board_array_size,
    coord_to_point,
    is_black_white,
    is_black_white_empty,
    opponent,
    where1d,
    BLACK,
    WHITE,
    EMPTY,
    BORDER,
    MAXSIZE,
    NO_POINT,
    PASS,
    GO_COLOR,
    GO_POINT,
)


"""
The GoBoard class implements a board and basic functions to play
moves, check the end of the game, and count the acore at the end.
The class also contains basic utility functions for writing a Go player.
For many more utility functions, see the GoBoardUtil class in board_util.py.

The board is stored as a one-dimensional array of GO_POINT in self.board.
See coord_to_point for explanations of the array encoding.
"""
class GoBoard(object):
    def __init__(self, size: int) -> None:
        """
        Creates a Go board of given size
        """
        assert 2 <= size <= MAXSIZE
        self.reset(size)

    def reset(self, size: int) -> None:
        """
        Creates a start state, an empty board with given size.
        """
        self.size: int = size
        self.NS: int = size + 1
        self.WE: int = 1
        self.ko_recapture: GO_POINT = NO_POINT
        self.last_move: GO_POINT = NO_POINT
        self.last2_move: GO_POINT = NO_POINT
        self.current_player: GO_COLOR = BLACK
        self.maxpoint: int = board_array_size(size)
        self.board: np.ndarray[GO_POINT] = np.full(self.maxpoint, BORDER, dtype=GO_POINT)
        self.liberty_of: np.ndarray[GO_POINT] = np.full(self.maxpoint, NO_POINT, dtype=GO_POINT)
        self._initialize_empty_points(self.board)
        self._initialize_neighbors()

    def copy(self) -> 'GoBoard':
        b = GoBoard(self.size)
        assert b.NS == self.NS
        assert b.WE == self.WE
        b.ko_recapture = self.ko_recapture
        b.last_move = self.last_move
        b.last2_move = self.last2_move
        b.current_player = self.current_player
        assert b.maxpoint == self.maxpoint
        b.board = np.copy(self.board)
        return b

    def get_color(self, point: GO_POINT) -> GO_COLOR:
        return self.board[point]

    def pt(self, row: int, col: int) -> GO_POINT:
        return coord_to_point(row, col, self.size)

    def _is_legal_check_simple_cases(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check the simple cases of illegal moves.
        Some "really bad" arguments will just trigger an assertion.
        If this function returns False: move is definitely illegal
        If this function returns True: still need to check more
        complicated cases such as suicide.
        """
        assert is_black_white(color)
        if point == PASS:
            return True
        # Could just return False for out-of-bounds, 
        # but it is better to know if this is called with an illegal point
        assert self.pt(1, 1) <= point <= self.pt(self.size, self.size)
        assert is_black_white_empty(self.board[point])
        if self.board[point] != EMPTY:
            return False
        if point == self.ko_recapture:
            return False
        return True

    def is_legal(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check whether it is legal for color to play on point
        """
        if point == PASS:
            return True
        if not self._is_legal_check_simple_cases(point, color):
            return False

        # General case: detect captures, suicide
        # A stone is placed temporarily, then removed again
        opp_color = opponent(color)
        self.board[point] = color
        legal = True
        has_capture = self._detect_captures(point, opp_color)
        if not has_capture and not self._stone_has_liberty(point):
            block = self._block_of(point)
            if not self._has_liberty(block, readOnly=True): # suicide
                legal = False
        self.board[point] = EMPTY
        return legal

    def end_of_game(self) -> bool:
        return self.last_move == PASS \
           and self.last2_move == PASS
           
    def _detect_captures(self, point: GO_POINT, opp_color: GO_COLOR) -> bool:
        """
        Did move on point capture something?
        """
        for nb in self.neighbors_of_color(point, opp_color):
            if self._detect_capture(nb):
                return True
        return False

    def get_empty_points(self) -> np.ndarray:
        """
        Return:
            The empty points on the board
        """
        return where1d(self.board == EMPTY)

    def get_color_points(self, color) -> np.ndarray:
        """
        Return:
            The points of the given color on the board
        """
        assert is_black_white_empty(color)
        return where1d(self.board == color)

    def row_start(self, row: int) -> int:
        assert row >= 1
        assert row <= self.size
        return row * self.NS + 1

    def _initialize_empty_points(self, board_array: np.ndarray) -> None:
        """
        Fills points on the board with EMPTY
        Argument
        ---------
        board: numpy array, filled with BORDER
        """
        for row in range(1, self.size + 1):
            start: int = self.row_start(row)
            board_array[start : start + self.size] = EMPTY

    def _on_board_neighbors(self, point: GO_POINT) -> List:
        nbs: List[GO_POINT] = []
        for nb in self._neighbors(point):
            if self.board[nb] != BORDER:
                nbs.append(nb)
        return nbs

    def _initialize_neighbors(self) -> None:
        """
        precompute neighbor array.
        For each point on the board, store its list of on-the-board neighbors
        """
        self.neighbors: List[List[GO_POINT]] = []
        for point in range(self.maxpoint):
            if self.board[point] == BORDER:
                self.neighbors.append([])
            else:
                self.neighbors.append(self._on_board_neighbors(GO_POINT(point)))

    def is_eye(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Check if point is a simple eye for color
        """
        if not self._is_surrounded(point, color):
            return False
        # Eye-like shape. Check diagonals to detect false eye
        opp_color = opponent(color)
        false_count = 0
        at_edge = 0
        for d in self._diag_neighbors(point):
            if self.board[d] == BORDER:
                at_edge = 1
            elif self.board[d] == opp_color:
                false_count += 1
        return false_count <= 1 - at_edge  # 0 at edge, 1 in center

    def _is_surrounded(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        check whether empty point is surrounded by stones of color.
        """
        for nb in self.neighbors[point]:
            nb_color = self.board[nb]
            if nb_color != color:
                return False
        return True

    def _stone_has_liberty(self, stone: GO_POINT) -> bool:
        lib = self.find_neighbor_of_color(stone, EMPTY)
        return lib != NO_POINT

    def _get_liberty(self, block: np.ndarray) -> GO_POINT:
        """
        Find any liberty of the given block.
        Returns NO_POINT in case there is no liberty.
        block is a numpy boolean array
        """
        for stone in where1d(block):
            lib: GO_POINT = self.find_neighbor_of_color(stone, EMPTY)
            if lib != NO_POINT:
                return lib
        return NO_POINT

    def _has_liberty(self, block: np.ndarray, readOnly: bool = False) -> bool:
        """
        Check if the given block has any liberty.
        Returns boolean.
        Input: block is a numpy boolean array
               readOnly is a boolean
        If readOnly=False:
            Also update the liberty cache: self.liberty_of
        """
        lib: GO_POINT = self._get_liberty(block)
        if lib == NO_POINT:
            return False
        assert self.get_color(lib) == EMPTY
        if not readOnly:
            for stone in where1d(block):
                self.liberty_of[stone] = lib
        return True

    def _block_of(self, stone: GO_POINT) -> np.ndarray:
        """
        Find the block of given stone
        Returns a board of boolean markers which are set for
        all the points in the block 
        """
        color: GO_COLOR = self.get_color(stone)
        assert is_black_white(color)
        return self.connected_component(stone)

    def connected_component(self, point: GO_POINT) -> np.ndarray:
        """
        Find the connected component of the given point.
        """
        marker = np.full(self.maxpoint, False, dtype=np.bool_)
        pointstack = [point]
        color: GO_COLOR = self.get_color(point)
        assert is_black_white_empty(color)
        marker[point] = True
        while pointstack:
            p = pointstack.pop()
            neighbors = self.neighbors_of_color(p, color)
            for nb in neighbors:
                if not marker[nb]:
                    marker[nb] = True
                    pointstack.append(nb)
        return marker

    def _liberty(self, point: GO_POINT, color: GO_COLOR) -> int:
        """
        Returns number of liberties of point
        """
        num_lib, _ = self._liberty_point(point, color)
        return num_lib

    def _liberty_point(self, point: GO_POINT, color: GO_COLOR) -> Tuple[int, GO_POINT]:
        """
        Helper function for returning number of liberty and
        last liberty for the point
        """
        assert color == self.get_color(point)
        group_points = [point]
        liberty = 0
        met_points = [point]
        while group_points:
            p = group_points.pop()
            met_points.append(p)
            neighbors = self.neighbors[p]
            for n in neighbors:
                if n not in met_points:
                    assert self.board[n] != BORDER
                    if self.board[n] == color:
                        group_points.append(n)
                    elif self.board[n] == EMPTY:
                        liberty += 1
                        single_lib_point = n
                    met_points.append(n)
        if liberty == 1:
            return liberty, single_lib_point
        return liberty, NO_POINT

    def get_block_liberty(self, point, color):
        """
        Find the number of liberty and points inside the block
        for the given point.
        This method is derived from _liberty_point
        """
        assert color == self.get_color(point)
        group_points = [point]
        liberty = 0
        met_points = [point]
        while group_points:
            p = group_points.pop()
            met_points.append(p)
            neighbors = self.neighbors[p]
            for n in neighbors:
                if n not in met_points:
                    assert self.board[n] != BORDER
                    if self.board[n] == color:
                        group_points.append(n)
                    elif self.board[n] == EMPTY:
                        liberty += 1
                    met_points.append(n)
        return liberty, met_points

    def _fast_liberty_check(self, nb_point: GO_POINT) -> bool:
        lib = self.liberty_of[nb_point]
        if lib != NO_POINT and self.get_color(lib) == EMPTY:
            return True  # quick exit, block has a liberty
        if self._stone_has_liberty(nb_point):
            return True  # quick exit, no need to look at whole block
        return False

    def _detect_capture(self, nb_point: GO_POINT) -> bool:
        """
        Check whether opponent block on nb_point is captured.
        Returns boolean.
        """
        if self._fast_liberty_check(nb_point):
            return False
        opp_block = self._block_of(nb_point)
        return not self._has_liberty(opp_block)

    def _detect_and_process_capture(self, nb_point: GO_POINT) -> GO_POINT:
        """
        Check whether opponent block on nb_point is captured.
        If yes, remove the stones.
        Returns the stone if only a single stone was captured,
        and returns NO_POINT otherwise.
        This result is used in play_move to check for possible ko
        """
        if self._fast_liberty_check(nb_point):
            return NO_POINT
        opp_block = self._block_of(nb_point)
        if self._has_liberty(opp_block):
            return NO_POINT
        captures = list(where1d(opp_block))
        self.board[captures] = EMPTY
        self.liberty_of[captures] = NO_POINT
        single_capture = NO_POINT
        if len(captures) == 1:
            single_capture = nb_point
        return single_capture

    def play_move(self, point: GO_POINT, color: GO_COLOR) -> bool:
        """
        Play a move of color on point
        Returns whether move was legal
        """
        if not self._is_legal_check_simple_cases(point, color):
            return False
        if point == PASS:
            self.ko_recapture = NO_POINT
            self.current_player = opponent(color)
            self.last2_move = self.last_move
            self.last_move = point
            return True

        # General case: deal with captures, suicide, and next ko point
        opp_color = opponent(color)
        in_enemy_eye = self._is_surrounded(point, opp_color)
        self.board[point] = color
        single_captures = []
        neighbors = self.neighbors[point]
        for nb in neighbors:
            if self.board[nb] == opp_color:
                single_capture = self._detect_and_process_capture(nb)
                if single_capture != NO_POINT:
                    single_captures.append(single_capture)
        if not self._stone_has_liberty(point):
            # check suicide of whole block
            block = self._block_of(point)
            if not self._has_liberty(block):  # undo suicide move
                self.board[point] = EMPTY
                return False
        self.ko_recapture = NO_POINT
        if in_enemy_eye and len(single_captures) == 1:
            self.ko_recapture = single_captures[0]
        self.current_player = opponent(color)
        self.last2_move = self.last_move
        self.last_move = point
        return True

    def neighbors_of_color(self, point: GO_POINT, color: GO_COLOR) -> List:
        """ List of neighbors of point of given color """
        nbc: List[GO_POINT] = []
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                nbc.append(nb)
        return nbc

    def find_neighbor_of_color(self, point: GO_POINT, color: GO_COLOR) -> GO_POINT:
        """ Return one neighbor of point of given color, if exists
            returns NO_POINT otherwise. 
        """
        for nb in self.neighbors[point]:
            if self.get_color(nb) == color:
                return nb
        return NO_POINT

    def _neighbors(self, point: GO_POINT) -> List:
        """ List of all four neighbors of the point """
        return [point - 1, point + 1, point - self.NS, point + self.NS]

    def _diag_neighbors(self, point: GO_POINT) -> List:
        """ List of all four diagonal neighbors of point """
        return [
            point - self.NS - 1,
            point - self.NS + 1,
            point + self.NS - 1,
            point + self.NS + 1,
        ]

    def last_board_moves(self) -> List:
        """
        Get the list of last_move and second last move.
        Only include moves on the board (not NO_POINT, not PASS).
        """
        board_moves: List[GO_POINT] = []
        if self.last_move != NO_POINT and self.last_move != PASS:
            board_moves.append(self.last_move)
        if self.last2_move != NO_POINT and self.last2_move != PASS:
            board_moves.append(self.last2_move)
        return board_moves
