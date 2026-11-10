from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum

BOARD_SIZE = 5
MAX_NON_CAPTURE_MOVES = 100
Position = tuple[int, int]


class Piece(IntEnum):
    CHILD = -1
    EMPTY = 0
    TIGER = 1


class Player(IntEnum):
    CHILD = Piece.CHILD
    TIGER = Piece.TIGER

    @property
    def opponent(self) -> Player:
        return Player.CHILD if self is Player.TIGER else Player.TIGER


BoardMatrix = list[list[Piece]]
PositionKey = tuple[tuple[int, ...] | int, ...]


@dataclass(frozen=True)
class Move:
    start: Position
    end: Position
    captured: Position | None = None

    @property
    def is_capture(self) -> bool:
        return self.captured is not None


def initial_board() -> BoardMatrix:
    board = [[Piece.EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
    for row in range(3):
        for column in range(BOARD_SIZE):
            board[row][column] = Piece.CHILD
    for column in (0, 2, 4):
        board[4][column] = Piece.TIGER
    return board


def copy_board(board: BoardMatrix) -> BoardMatrix:
    validate_board(board)
    return [[Piece(cell) for cell in row] for row in board]


def validate_board(board: BoardMatrix) -> None:
    if len(board) != BOARD_SIZE or any(len(row) != BOARD_SIZE for row in board):
        raise ValueError(f"board must be {BOARD_SIZE}x{BOARD_SIZE}")
    for row in board:
        for cell in row:
            try:
                Piece(cell)
            except ValueError as error:
                raise ValueError(f"invalid board value: {cell!r}") from error


def in_bounds(position: Position) -> bool:
    row, column = position
    return 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE


def _moves_for_piece(board: BoardMatrix, start: Position) -> list[Move]:
    if not in_bounds(start):
        return []

    row, column = start
    piece = Piece(board[row][column])
    if piece is Piece.EMPTY:
        return []

    moves: list[Move] = []
    for row_step, column_step in ((-1, 0), (1, 0), (0, -1), (0, 1)):
        adjacent = (row + row_step, column + column_step)
        if in_bounds(adjacent) and board[adjacent[0]][adjacent[1]] == Piece.EMPTY:
            moves.append(Move(start=start, end=adjacent))

        if piece is not Piece.TIGER:
            continue

        target = (row + row_step * 2, column + column_step * 2)
        if (
            in_bounds(target)
            and board[adjacent[0]][adjacent[1]] == Piece.EMPTY
            and board[target[0]][target[1]] == Piece.CHILD
        ):
            moves.append(Move(start=start, end=target, captured=target))

    return moves


def legal_moves_for_piece(board: BoardMatrix, start: Position) -> list[Move]:
    validate_board(board)
    return _moves_for_piece(board, start)


def legal_moves(board: BoardMatrix, player: Player) -> list[Move]:
    validate_board(board)
    return _legal_moves(board, Player(player))


def _legal_moves(board: BoardMatrix, player: Player) -> list[Move]:
    player = Player(player)
    moves: list[Move] = []
    for row in range(BOARD_SIZE):
        for column in range(BOARD_SIZE):
            if board[row][column] == player:
                moves.extend(_moves_for_piece(board, (row, column)))
    return moves


def find_legal_move(board: BoardMatrix, start: Position, end: Position) -> Move | None:
    for move in legal_moves_for_piece(board, start):
        if move.end == end:
            return move
    return None


def apply_move(board: BoardMatrix, move: Move) -> BoardMatrix:
    """Apply a legal move and return a new board.

    A tiger eats the child standing on its landing square, so ``captured``
    always equals ``end``. Passing a different ``captured`` square is a bug.
    """
    canonical_move = find_legal_move(board, move.start, move.end)
    if canonical_move is None:
        raise ValueError(f"illegal move: {move.start} -> {move.end}")
    if move.captured is not None and move.captured != canonical_move.end:
        raise ValueError(
            f"captured square {move.captured} must be the landing square "
            f"{canonical_move.end}"
        )

    updated = copy_board(board)
    start_row, start_column = canonical_move.start
    end_row, end_column = canonical_move.end
    moving_piece = Piece(updated[start_row][start_column])
    updated[start_row][start_column] = Piece.EMPTY
    if canonical_move.captured is not None:
        captured_row, captured_column = canonical_move.captured
        if updated[captured_row][captured_column] is not Piece.CHILD:
            raise ValueError(f"no child to capture at {canonical_move.captured}")
        updated[captured_row][captured_column] = Piece.EMPTY
    updated[end_row][end_column] = moving_piece
    return updated


def count_pieces(board: BoardMatrix, piece: Piece) -> int:
    validate_board(board)
    return _count_pieces(board, piece)


def _count_pieces(board: BoardMatrix, piece: Piece) -> int:
    return sum(cell == piece for row in board for cell in row)


def winner(board: BoardMatrix) -> Player | None:
    """Return the winner of a position, or ``None`` if the game continues.

    The check ignores whose turn it is: a side without any legal move has
    lost. If both sides are stuck the child side wins, because the tiger
    check runs first.
    """
    validate_board(board)
    if _count_pieces(board, Piece.CHILD) == 0:
        return Player.TIGER
    if not _legal_moves(board, Player.TIGER):
        return Player.CHILD
    if not _legal_moves(board, Player.CHILD):
        return Player.TIGER
    return None


def position_key(board: BoardMatrix, player: Player) -> PositionKey:
    validate_board(board)
    rows = tuple(tuple(int(cell) for cell in row) for row in board)
    return (*rows, int(player))


@dataclass
class GameState:
    board: BoardMatrix = field(default_factory=initial_board)
    current_player: Player = Player.TIGER
    max_non_capture_moves: int = MAX_NON_CAPTURE_MOVES
    winning_player: Player | None = field(init=False, default=None)
    is_draw: bool = field(init=False, default=False)
    move_count: int = 0
    non_capture_move_count: int = 0
    position_counts: dict[PositionKey, int] = field(
        init=False, default_factory=dict, repr=False
    )

    def __post_init__(self) -> None:
        if self.max_non_capture_moves < 1:
            raise ValueError("max_non_capture_moves must be at least 1")
        self.board = copy_board(self.board)
        self.current_player = Player(self.current_player)
        self.winning_player = winner(self.board)
        self._record_position()

    @property
    def is_over(self) -> bool:
        return self.winning_player is not None or self.is_draw

    def _record_position(self) -> None:
        key = position_key(self.board, self.current_player)
        self.position_counts[key] = self.position_counts.get(key, 0) + 1
        if self.position_counts[key] >= 3:
            self.is_draw = True

    def moves_from(self, start: Position) -> list[Move]:
        if self.is_over or not in_bounds(start):
            return []
        row, column = start
        if self.board[row][column] != self.current_player:
            return []
        return legal_moves_for_piece(self.board, start)

    def play(self, start: Position, end: Position) -> Move:
        if self.is_over:
            raise ValueError("the game is already over")
        if not in_bounds(start):
            raise ValueError(f"position is outside the board: {start}")
        if self.board[start[0]][start[1]] != self.current_player:
            raise ValueError("the selected piece does not belong to the current player")

        move = find_legal_move(self.board, start, end)
        if move is None:
            raise ValueError(f"illegal move: {start} -> {end}")

        self.board = apply_move(self.board, move)
        self.move_count += 1
        if move.is_capture:
            self.non_capture_move_count = 0
        else:
            self.non_capture_move_count += 1
        self.winning_player = winner(self.board)
        if self.winning_player is None:
            self.current_player = self.current_player.opponent
            self._record_position()
            if self.non_capture_move_count >= self.max_non_capture_moves:
                self.is_draw = True
        return move
