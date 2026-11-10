"""单人模式的电脑对手：alpha-beta + 迭代加深。

这个棋分支不多、战术直白（吃子就是两格外跳过去），同样时间里 alpha-beta
比 MCTS 强得多，也不需要随机模拟。搜索只用 ``rules`` 里的纯函数，不碰
``GameState`` 的历史。
"""

from __future__ import annotations

import random
import time
from dataclasses import dataclass

from rules import (
    CHILD,
    DRAW_PLIES,
    EMPTY,
    INITIAL_CHILDREN,
    JUMPS,
    NEIGHBORS,
    TIGER,
    Board,
    GameState,
    Move,
    PositionKey,
    apply_move,
    count_pieces,
    is_capture,
    legal_moves,
    opponent,
)

MATE = 100_000
INF = 1_000_000


@dataclass(frozen=True)
class Level:
    max_depth: int
    budget: float
    random_chance: float = 0.0


LEVELS = {
    "easy": Level(max_depth=2, budget=0.05, random_chance=0.35),
    "normal": Level(max_depth=5, budget=0.20),
    "hard": Level(max_depth=8, budget=0.50),
}


class _Timeout(Exception):
    pass


class _Search:
    def __init__(
        self,
        board: Board,
        player: int,
        counts: dict[PositionKey, int],
        non_capture: int,
        deadline: float,
    ) -> None:
        self.board = board
        self.player = player
        self.counts = counts
        self.non_capture = non_capture
        self.deadline = deadline
        self.nodes = 0

    def run(self, max_depth: int) -> Move | None:
        best: Move | None = None
        for depth in range(1, max_depth + 1):
            self.nodes = 0
            try:
                score, move = self._root(depth)
            except _Timeout:
                break
            best = move
            if abs(score) >= MATE - 100:
                break
        return best

    def _root(self, depth: int) -> tuple[int, Move]:
        moves = legal_moves(self.board, self.player)
        moves.sort(key=is_capture, reverse=True)
        alpha = -INF
        best_score = -INF
        best_move = moves[0]
        for move in moves:
            if time.monotonic() > self.deadline:
                raise _Timeout
            child = apply_move(self.board, move)
            child_player = opponent(self.player)
            key, playable = self._push(child, child_player)
            if playable:
                child_count = 0 if is_capture(move) else self.non_capture + 1
                try:
                    score = -self._negamax(
                        child,
                        child_player,
                        depth - 1,
                        -INF,
                        -alpha,
                        child_count,
                        1,
                    )
                finally:
                    self._pop(key)
            else:
                score = 0
            if score > best_score:
                best_score = score
                best_move = move
            if score > alpha:
                alpha = score
        return best_score, best_move

    def _negamax(
        self,
        board: Board,
        player: int,
        depth: int,
        alpha: int,
        beta: int,
        non_capture: int,
        ply: int,
    ) -> int:
        self.nodes += 1
        if self.nodes & 1023 == 0 and time.monotonic() > self.deadline:
            raise _Timeout

        if count_pieces(board, CHILD) == 0:
            return MATE - ply if player == TIGER else -MATE + ply
        moves = legal_moves(board, player)
        if not moves:
            return -MATE + ply
        if non_capture >= DRAW_PLIES:
            return 0
        if depth <= 0:
            return self._evaluate(board, player)

        moves.sort(key=is_capture, reverse=True)
        best = -INF
        for move in moves:
            child = apply_move(board, move)
            child_player = opponent(player)
            key, playable = self._push(child, child_player)
            if playable:
                child_count = 0 if is_capture(move) else non_capture + 1
                try:
                    score = -self._negamax(
                        child,
                        child_player,
                        depth - 1,
                        -beta,
                        -alpha,
                        child_count,
                        ply + 1,
                    )
                finally:
                    self._pop(key)
            else:
                score = 0
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best

    def _push(self, board: Board, player: int) -> tuple[PositionKey, bool]:
        key = (board, player)
        count = self.counts.get(key, 0) + 1
        if count >= 3:
            return key, False
        self.counts[key] = count
        return key, True

    def _pop(self, key: PositionKey) -> None:
        count = self.counts[key] - 1
        if count:
            self.counts[key] = count
        else:
            del self.counts[key]

    @staticmethod
    def _evaluate(board: Board, player: int) -> int:
        children = 0
        tiger_mobility = 0
        child_mobility = 0
        threats = 0
        stuck = 0
        cramped = 0
        for cell, piece in enumerate(board):
            if piece == TIGER:
                moves = 0
                for end in NEIGHBORS[cell]:
                    if board[end] == EMPTY:
                        moves += 1
                for mid, end in JUMPS[cell]:
                    if board[mid] == EMPTY and board[end] == CHILD:
                        moves += 1
                        threats += 1
                tiger_mobility += moves
                if moves == 0:
                    stuck += 1
                elif moves == 1:
                    cramped += 1
            elif piece == CHILD:
                children += 1
                for end in NEIGHBORS[cell]:
                    if board[end] == EMPTY:
                        child_mobility += 1

        score = (
            (INITIAL_CHILDREN - children) * 1000
            + (tiger_mobility - child_mobility) * 8
            + threats * 150
            - stuck * 600
            - cramped * 200
        )
        return score if player == TIGER else -score


def choose_move(
    game: GameState,
    level: str = "normal",
    rng: random.Random | None = None,
) -> Move | None:
    if game.is_over:
        return None
    moves = legal_moves(game.board, game.player)
    if not moves:
        return None
    if len(moves) == 1:
        return moves[0]

    config = LEVELS[level]
    if rng is None:
        rng = random.Random()
    if config.random_chance and rng.random() < config.random_chance:
        return rng.choice(moves)

    search = _Search(
        game.board,
        game.player,
        dict(game.positions),
        game.non_capture,
        time.monotonic() + config.budget,
    )
    return search.run(config.max_depth) or moves[0]
