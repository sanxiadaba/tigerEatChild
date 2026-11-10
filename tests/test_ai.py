import random
import unittest

from ai import LEVELS, choose_move
from rules import (
    CHILD,
    EMPTY,
    TIGER,
    GameState,
    apply_move,
    count_pieces,
    legal_moves,
)

PIECES = {".": EMPTY, "C": CHILD, "T": TIGER}


def board(text: str):
    flat = "".join(text.split())
    assert len(flat) == 25, len(flat)
    return bytes(PIECES[char] for char in flat)


class AiTests(unittest.TestCase):
    def test_returns_a_legal_move_for_each_level(self):
        game = GameState()

        for level in LEVELS:
            with self.subTest(level=level):
                move = choose_move(game, level, random.Random(0))
                self.assertIsNotNone(move)
                self.assertIn(move, legal_moves(game.board, game.player))

    def test_takes_a_free_capture_and_wins(self):
        game = GameState(board=board("..... ..... ..C.. ..... ..T.."))

        move = choose_move(game, "hard", random.Random(0))

        self.assertEqual(move, (22, 12))
        self.assertEqual(count_pieces(apply_move(game.board, move), CHILD), 0)

    def test_does_not_mutate_the_game(self):
        game = GameState()
        before = (
            game.board,
            game.player,
            game.non_capture,
            game.move_count,
            dict(game.positions),
            len(game.history),
        )

        choose_move(game, "normal", random.Random(0))

        after = (
            game.board,
            game.player,
            game.non_capture,
            game.move_count,
            dict(game.positions),
            len(game.history),
        )
        self.assertEqual(before, after)

    def test_returns_none_when_the_game_is_over(self):
        game = GameState(board=board("..... ..... ..... ..... T.T.T"))

        self.assertTrue(game.is_over)
        self.assertIsNone(choose_move(game, "normal"))

    def test_can_play_the_child_side(self):
        game = GameState()
        game.play((20, 15))
        self.assertEqual(game.player, CHILD)

        move = choose_move(game, "normal", random.Random(0))

        self.assertIsNotNone(move)
        self.assertIn(move, legal_moves(game.board, CHILD))


if __name__ == "__main__":
    unittest.main()
