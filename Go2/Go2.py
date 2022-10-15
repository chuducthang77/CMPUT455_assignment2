#!/usr/local/bin/python3
# /usr/bin/python3
# Set the path to your python3 above

from board_base import DEFAULT_SIZE, GO_POINT, GO_COLOR
from board import GoBoard
from board_util import GoBoardUtil
from engine import GoEngine
from gtp_connection_go2 import GtpConnectionGo2


class Go2(GoEngine):
    def __init__(self) -> None:
        """
        Go player that selects moves randomly from the set of legal moves.
        However, it filters eye-filling moves.
        Passes only if there is no other legal move.
        """
        GoEngine.__init__(self, "Go2", 1.0)

    def get_move(self, board: GoBoard, color: GO_COLOR) -> GO_POINT:
        return GoBoardUtil.generate_random_move(board, color, True)


def run() -> None:
    """
    start the gtp connection and wait for commands.
    """
    board = GoBoard(DEFAULT_SIZE)
    con = GtpConnectionGo2(Go2(), board)
    con.start_connection()


if __name__ == "__main__":
    run()
