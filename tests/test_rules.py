import unittest

from rules import (
    CHILD,
    DRAW_PLIES,
    EMPTY,
    TIGER,
    GameState,
    apply_move,
    count_pieces,
    game_winner,
    initial_board,
    is_capture,
    legal_moves,
    moves_from,
    position_key,
    validate_board,
)

PIECES = {".": EMPTY, "C": CHILD, "T": TIGER}


def board(text: str):
    flat = "".join(text.split())
    assert len(flat) == 25, len(flat)
    return bytes(PIECES[char] for char in flat)


class RulesTests(unittest.TestCase):
    def test_initial_layout(self):
        state = GameState()

        self.assertEqual(count_pieces(state.board, CHILD), 15)
        self.assertEqual(count_pieces(state.board, TIGER), 3)
        self.assertEqual([state.board[index] for index in (20, 22, 24)], [TIGER] * 3)
        self.assertEqual(state.player, TIGER)
        self.assertFalse(state.is_over)

    def test_child_moves_one_step(self):
        state = GameState()
        self.assertEqual(moves_from(state.board, 10), [(10, 15)])
        self.assertEqual(len(legal_moves(state.board, CHILD)), 5)

    def test_tiger_steps_and_captures(self):
        moves = moves_from(initial_board(), 20)

        self.assertIn((20, 15), moves)
        self.assertIn((20, 21), moves)
        self.assertIn((20, 10), moves)
        self.assertTrue(is_capture((20, 10)))
        self.assertFalse(is_capture((20, 15)))

    def test_tiger_cannot_jump_over_a_child(self):
        state = GameState(board=board("..... ..... ..... C.... T...."))

        self.assertNotIn(10, [end for _, end in moves_from(state.board, 20)])

    def test_adjacent_child_cannot_be_captured(self):
        state = GameState(board=board("..... ..... ..TC. ..... ....."))

        ends = [end for _, end in moves_from(state.board, 12)]

        self.assertNotIn(13, ends)

    def test_capture_removes_child_and_wins(self):
        state = GameState(board=board("..... ..... ..C.. ..... ..T.."))

        move = state.play((22, 12))

        self.assertTrue(is_capture(move))
        self.assertEqual(state.board[22], EMPTY)
        self.assertEqual(state.board[12], TIGER)
        self.assertEqual(count_pieces(state.board, CHILD), 0)
        self.assertEqual(state.winner, TIGER)
        self.assertEqual(state.end_reason, "tiger_eats_all")

    def test_turn_alternates(self):
        state = GameState()

        state.play((20, 15))
        self.assertEqual(state.player, CHILD)
        state.play((11, 16))
        self.assertEqual(state.player, TIGER)
        self.assertEqual(state.move_count, 2)

    def test_threefold_repetition_is_a_draw(self):
        state = GameState()
        cycle = ((20, 15), (11, 16), (15, 20), (16, 11))

        for _ in range(2):
            for move in cycle:
                state.play(move)

        self.assertTrue(state.draw)
        self.assertTrue(state.is_over)
        self.assertIsNone(state.winner)
        self.assertEqual(state.end_reason, "repetition")
        with self.assertRaisesRegex(ValueError, "over"):
            state.play((20, 15))

    def test_no_capture_limit_is_configurable(self):
        state = GameState(max_non_capture=2)

        state.play((20, 15))
        self.assertFalse(state.draw)
        state.play((11, 16))

        self.assertTrue(state.draw)
        self.assertEqual(state.end_reason, "no_capture")
        self.assertEqual(DRAW_PLIES, 100)

    def test_non_capture_limit_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            GameState(max_non_capture=0)

    def test_stuck_tiger_only_loses_when_it_is_the_tigers_turn(self):
        start = board("TC... C.... ..... ..... .....")

        waiting = GameState(board=start, player=CHILD)
        self.assertFalse(waiting.is_over)
        waiting.play((1, 2))
        self.assertFalse(waiting.is_over)
        self.assertIn((0, 1), waiting.moves_from(0))

        stuck = GameState(board=start, player=TIGER)
        self.assertEqual(stuck.winner, CHILD)
        self.assertEqual(stuck.end_reason, "tiger_stuck")

    def test_stuck_child_is_a_tiger_win(self):
        state = GameState(board=board("CT... T.... ..... ..... ....."), player=CHILD)

        self.assertEqual(state.winner, TIGER)
        self.assertEqual(state.end_reason, "child_stuck")

    def test_no_children_is_a_tiger_win(self):
        state = GameState(board=board("..... ..... ..... ..... T.T.T"))

        self.assertEqual(state.winner, TIGER)
        self.assertEqual(state.end_reason, "tiger_eats_all")

    def test_apply_move_does_not_mutate_the_input(self):
        start = initial_board()

        updated = apply_move(start, (20, 15))

        self.assertEqual(start[20], TIGER)
        self.assertEqual(start[15], EMPTY)
        self.assertEqual(updated[20], EMPTY)
        self.assertEqual(updated[15], TIGER)

    def test_illegal_moves_are_rejected(self):
        state = GameState()

        with self.assertRaisesRegex(ValueError, "current player"):
            state.play((10, 15))
        with self.assertRaisesRegex(ValueError, "illegal move"):
            state.play((20, 16))
        with self.assertRaisesRegex(ValueError, "outside"):
            state.play((20, 99))

    def test_board_validation(self):
        with self.assertRaisesRegex(ValueError, "25 cells"):
            validate_board(b"\x00" * 24)
        with self.assertRaisesRegex(ValueError, "0, 1 or 2"):
            validate_board(bytes([3]) + b"\x00" * 24)

    def test_undo_restores_the_previous_position(self):
        state = GameState()
        state.play((20, 15))

        self.assertTrue(state.undo())
        self.assertEqual(state.board, initial_board())
        self.assertEqual(state.player, TIGER)
        self.assertEqual(state.move_count, 0)
        self.assertIsNone(state.last_move)
        self.assertFalse(state.undo())

    def test_undo_after_a_finished_game(self):
        state = GameState(board=board("..... ..... ..C.. ..... ..T.."))
        state.play((22, 12))

        state.undo()

        self.assertFalse(state.is_over)
        self.assertIsNone(state.winner)
        self.assertEqual(state.player, TIGER)
        self.assertEqual(count_pieces(state.board, CHILD), 1)

    def test_position_key_includes_the_player(self):
        start = initial_board()

        self.assertNotEqual(position_key(start, TIGER), position_key(start, CHILD))

    def test_game_winner_ignores_the_side_that_is_not_to_move(self):
        start = board("TC... C.... ..... ..... .....")

        self.assertIsNone(game_winner(start, CHILD))
        self.assertEqual(game_winner(start, TIGER), CHILD)


if __name__ == "__main__":
    unittest.main()
