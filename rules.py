"""棋盘规则：5x5，三只老虎对十五个小孩。

棋盘是 25 个字节的不可变序列，0 空、1 小孩、2 老虎，下标是 ``row * 5 + column``。
走法就是 ``(起点, 终点)`` 两个下标；吃子永远是落点，不需要额外字段。
"""

from __future__ import annotations

from dataclasses import dataclass, field

BOARD_SIZE = 5
CELLS = BOARD_SIZE * BOARD_SIZE
EMPTY = 0
CHILD = 1
TIGER = 2
INITIAL_CHILDREN = 15
DRAW_PLIES = 100

Board = bytes
Move = tuple[int, int]
PositionKey = tuple[Board, int]


def opponent(player: int) -> int:
    return CHILD if player == TIGER else TIGER


def index(row: int, column: int) -> int:
    return row * BOARD_SIZE + column


def row_col(cell: int) -> tuple[int, int]:
    return divmod(cell, BOARD_SIZE)


def initial_board() -> Board:
    board = bytearray(CELLS)
    for row in range(3):
        for column in range(BOARD_SIZE):
            board[index(row, column)] = CHILD
    for column in (0, 2, 4):
        board[index(BOARD_SIZE - 1, column)] = TIGER
    return bytes(board)


def _build_tables() -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[tuple[int, int], ...], ...]]:
    neighbors: list[list[int]] = [[] for _ in range(CELLS)]
    jumps: list[list[tuple[int, int]]] = [[] for _ in range(CELLS)]
    for cell in range(CELLS):
        row, column = row_col(cell)
        for row_step, column_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            mid_row, mid_column = row + row_step, column + column_step
            if not (0 <= mid_row < BOARD_SIZE and 0 <= mid_column < BOARD_SIZE):
                continue
            mid = index(mid_row, mid_column)
            neighbors[cell].append(mid)
            end_row, end_column = mid_row + row_step, mid_column + column_step
            if 0 <= end_row < BOARD_SIZE and 0 <= end_column < BOARD_SIZE:
                jumps[cell].append((mid, index(end_row, end_column)))
    return tuple(tuple(items) for items in neighbors), tuple(tuple(items) for items in jumps)


NEIGHBORS, JUMPS = _build_tables()


def validate_board(board: Board) -> None:
    if len(board) != CELLS:
        raise ValueError(f"board must have {CELLS} cells")
    if any(cell not in (EMPTY, CHILD, TIGER) for cell in board):
        raise ValueError("board cells must be 0, 1 or 2")


def moves_from(board: Board, start: int) -> list[Move]:
    if not 0 <= start < CELLS:
        return []
    piece = board[start]
    if piece == EMPTY:
        return []

    moves: list[Move] = [(start, end) for end in NEIGHBORS[start] if board[end] == EMPTY]
    if piece == TIGER:
        moves.extend(
            (start, end) for mid, end in JUMPS[start] if board[mid] == EMPTY and board[end] == CHILD
        )
    return moves


def legal_moves(board: Board, player: int) -> list[Move]:
    moves: list[Move] = []
    for cell, piece in enumerate(board):
        if piece == player:
            moves.extend(moves_from(board, cell))
    return moves


def find_move(board: Board, start: int, end: int) -> Move | None:
    for move in moves_from(board, start):
        if move[1] == end:
            return move
    return None


def is_capture(move: Move) -> bool:
    return abs(move[0] - move[1]) in (2, 2 * BOARD_SIZE)


def apply_move(board: Board, move: Move) -> Board:
    start, end = move
    updated = bytearray(board)
    updated[start] = EMPTY
    updated[end] = board[start]
    return bytes(updated)


def count_pieces(board: Board, piece: int) -> int:
    return board.count(piece)


def position_key(board: Board, player: int) -> PositionKey:
    return board, player


def game_winner(board: Board, player: int) -> int | None:
    """Return the winner if the side to move is stuck, or the tiger ate every child."""
    if count_pieces(board, CHILD) == 0:
        return TIGER
    if not legal_moves(board, player):
        return opponent(player)
    return None


@dataclass(frozen=True)
class _Snapshot:
    board: Board
    player: int
    move_count: int
    non_capture: int
    winner: int | None
    draw: bool
    end_reason: str | None
    last_move: Move | None
    positions: dict[PositionKey, int]


@dataclass
class GameState:
    board: Board = field(default_factory=initial_board)
    player: int = TIGER
    max_non_capture: int = DRAW_PLIES
    move_count: int = 0
    non_capture: int = 0
    winner: int | None = field(init=False, default=None)
    draw: bool = field(init=False, default=False)
    end_reason: str | None = field(init=False, default=None)
    last_move: Move | None = field(init=False, default=None)
    positions: dict[PositionKey, int] = field(init=False, default_factory=dict, repr=False)
    history: list[_Snapshot] = field(init=False, default_factory=list, repr=False)

    def __post_init__(self) -> None:
        validate_board(self.board)
        if self.player not in (CHILD, TIGER):
            raise ValueError("player must be CHILD or TIGER")
        if self.max_non_capture < 1:
            raise ValueError("max_non_capture must be at least 1")
        if self.move_count < 0 or self.non_capture < 0:
            raise ValueError("counters must not be negative")
        self.board = bytes(self.board)

        self.winner = game_winner(self.board, self.player)
        if self.winner is not None:
            self.end_reason = self._reason_for_winner()
            return
        if self.non_capture >= self.max_non_capture:
            self.draw = True
            self.end_reason = "no_capture"
            return
        self.positions[position_key(self.board, self.player)] = 1

    @property
    def is_over(self) -> bool:
        return self.winner is not None or self.draw

    def legal_moves(self) -> list[Move]:
        if self.is_over:
            return []
        return legal_moves(self.board, self.player)

    def moves_from(self, start: int) -> list[Move]:
        if self.is_over or not 0 <= start < CELLS or self.board[start] != self.player:
            return []
        return moves_from(self.board, start)

    def play(self, move: Move) -> Move:
        if self.is_over:
            raise ValueError("the game is over")
        start, end = move
        if not (0 <= start < CELLS and 0 <= end < CELLS):
            raise ValueError(f"position is outside the board: {move}")
        if self.board[start] != self.player:
            raise ValueError("the selected piece does not belong to the current player")
        if find_move(self.board, start, end) is None:
            raise ValueError(f"illegal move: {start} -> {end}")

        self.history.append(self._snapshot())
        self.board = apply_move(self.board, move)
        self.move_count += 1
        self.last_move = move
        self.non_capture = 0 if is_capture(move) else self.non_capture + 1
        self.player = opponent(self.player)
        self._settle()
        return move

    def undo(self) -> bool:
        if not self.history:
            return False
        snapshot = self.history.pop()
        self.board = snapshot.board
        self.player = snapshot.player
        self.move_count = snapshot.move_count
        self.non_capture = snapshot.non_capture
        self.winner = snapshot.winner
        self.draw = snapshot.draw
        self.end_reason = snapshot.end_reason
        self.last_move = snapshot.last_move
        self.positions = dict(snapshot.positions)
        return True

    def _snapshot(self) -> _Snapshot:
        return _Snapshot(
            board=self.board,
            player=self.player,
            move_count=self.move_count,
            non_capture=self.non_capture,
            winner=self.winner,
            draw=self.draw,
            end_reason=self.end_reason,
            last_move=self.last_move,
            positions=dict(self.positions),
        )

    def _reason_for_winner(self) -> str:
        if count_pieces(self.board, CHILD) == 0:
            return "tiger_eats_all"
        if self.player == TIGER:
            return "tiger_stuck"
        return "child_stuck"

    def _settle(self) -> None:
        if count_pieces(self.board, CHILD) == 0:
            self.winner = TIGER
            self.end_reason = "tiger_eats_all"
            return
        if not legal_moves(self.board, self.player):
            self.winner = opponent(self.player)
            self.end_reason = "tiger_stuck" if self.winner == CHILD else "child_stuck"
            return

        key = position_key(self.board, self.player)
        count = self.positions.get(key, 0) + 1
        self.positions[key] = count
        if count >= 3:
            self.draw = True
            self.end_reason = "repetition"
            return
        if self.non_capture >= self.max_non_capture:
            self.draw = True
            self.end_reason = "no_capture"
