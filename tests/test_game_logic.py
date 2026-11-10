import unittest

from game_logic import (
    BOARD_SIZE,
    GameState,
    Move,
    Piece,
    Player,
    apply_move,
    count_pieces,
    initial_board,
    legal_moves_for_piece,
    validate_board,
    winner,
)


def empty_board():
    return [[Piece.EMPTY for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]


class GameLogicTests(unittest.TestCase):
    def test_initial_board_has_original_layout(self):
        board = initial_board()

        self.assertEqual(count_pieces(board, Piece.CHILD), 15)
        self.assertEqual(count_pieces(board, Piece.TIGER), 3)
        self.assertEqual(
            [board[4][column] for column in range(BOARD_SIZE)],
            [Piece.TIGER, Piece.EMPTY, Piece.TIGER, Piece.EMPTY, Piece.TIGER],
        )
        self.assertIsNone(winner(board))

    def test_child_can_only_move_one_step_to_an_empty_space(self):
        board = initial_board()
        moves = legal_moves_for_piece(board, (2, 0))

        self.assertEqual(moves, [Move(start=(2, 0), end=(3, 0))])

    def test_tiger_has_normal_and_capture_moves(self):
        board = initial_board()
        moves = legal_moves_for_piece(board, (4, 0))

        self.assertIn(Move(start=(4, 0), end=(3, 0)), moves)
        self.assertIn(Move(start=(4, 0), end=(4, 1)), moves)
        self.assertIn(Move(start=(4, 0), end=(2, 0), captured=(2, 0)), moves)

    def test_tiger_cannot_overwrite_an_adjacent_child(self):
        board = empty_board()
        board[2][2] = Piece.TIGER
        board[2][3] = Piece.CHILD

        destinations = {move.end for move in legal_moves_for_piece(board, (2, 2))}

        self.assertNotIn((2, 3), destinations)

    def test_capture_removes_child_and_moves_tiger(self):
        board = empty_board()
        board[4][2] = Piece.TIGER
        board[2][2] = Piece.CHILD
        game = GameState(board=board)

        move = game.play((4, 2), (2, 2))

        self.assertTrue(move.is_capture)
        self.assertEqual(game.board[4][2], Piece.EMPTY)
        self.assertEqual(game.board[2][2], Piece.TIGER)
        self.assertEqual(count_pieces(game.board, Piece.CHILD), 0)
        self.assertEqual(game.winning_player, Player.TIGER)

    def test_turn_changes_after_each_legal_move(self):
        game = GameState()

        game.play((4, 0), (3, 0))
        self.assertEqual(game.current_player, Player.CHILD)
        game.play((2, 1), (3, 1))
        self.assertEqual(game.current_player, Player.TIGER)
        self.assertEqual(game.move_count, 2)

    def test_threefold_repetition_is_a_draw(self):
        game = GameState()
        cycle = (
            ((4, 0), (3, 0)),
            ((2, 1), (3, 1)),
            ((3, 0), (4, 0)),
            ((3, 1), (2, 1)),
        )

        for _ in range(2):
            for start, end in cycle:
                game.play(start, end)

        self.assertTrue(game.is_draw)
        self.assertTrue(game.is_over)
        self.assertIsNone(game.winning_player)
        with self.assertRaisesRegex(ValueError, "already over"):
            game.play((4, 0), (3, 0))

    def test_non_capture_move_limit_is_configurable(self):
        game = GameState(max_non_capture_moves=2)

        game.play((4, 0), (3, 0))
        self.assertFalse(game.is_draw)
        game.play((2, 1), (3, 1))

        self.assertTrue(game.is_draw)
        self.assertTrue(game.is_over)
        self.assertIsNone(game.winning_player)

    def test_non_capture_move_limit_must_be_positive(self):
        with self.assertRaisesRegex(ValueError, "at least 1"):
            GameState(max_non_capture_moves=0)

    def test_both_sides_stuck_is_a_child_win(self):
        board = empty_board()
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                board[row][column] = Piece.CHILD
        board[0][0] = Piece.TIGER
        board[0][1] = Piece.TIGER
        board[0][2] = Piece.TIGER

        self.assertEqual(winner(board), Player.CHILD)

    def test_tiger_cannot_capture_through_an_occupied_middle_cell(self):
        board = empty_board()
        board[4][0] = Piece.TIGER
        board[3][0] = Piece.CHILD
        board[2][0] = Piece.CHILD

        destinations = {move.end for move in legal_moves_for_piece(board, (4, 0))}

        self.assertNotIn((2, 0), destinations)

    def test_apply_move_rejects_captured_square_that_is_not_the_landing_square(self):
        board = initial_board()

        with self.assertRaisesRegex(ValueError, "landing square"):
            apply_move(board, Move(start=(4, 0), end=(2, 0), captured=(1, 1)))

    def test_game_state_copies_the_input_board(self):
        board = initial_board()
        game = GameState(board=board)

        game.play((4, 0), (3, 0))

        self.assertEqual(board[4][0], Piece.TIGER)
        self.assertEqual(board[3][0], Piece.EMPTY)

    def test_wrong_player_and_illegal_moves_are_rejected(self):
        game = GameState()

        with self.assertRaisesRegex(ValueError, "current player"):
            game.play((2, 0), (3, 0))
        with self.assertRaisesRegex(ValueError, "illegal move"):
            game.play((4, 0), (3, 1))

    def test_children_win_when_all_tigers_are_blocked(self):
        board = empty_board()
        board[0][0] = Piece.TIGER
        for position in ((0, 1), (1, 0), (0, 2), (2, 0)):
            board[position[0]][position[1]] = Piece.CHILD

        self.assertEqual(winner(board), Player.CHILD)

    def test_tigers_win_when_children_cannot_move(self):
        board = empty_board()
        board[0][0] = Piece.CHILD
        board[0][1] = Piece.TIGER
        board[1][0] = Piece.TIGER

        self.assertEqual(winner(board), Player.TIGER)

    def test_apply_move_does_not_mutate_original_board(self):
        board = initial_board()

        updated = apply_move(board, Move(start=(4, 0), end=(3, 0)))

        self.assertEqual(board[4][0], Piece.TIGER)
        self.assertEqual(board[3][0], Piece.EMPTY)
        self.assertEqual(updated[4][0], Piece.EMPTY)
        self.assertEqual(updated[3][0], Piece.TIGER)

    def test_board_validation_rejects_bad_shape_and_values(self):
        with self.assertRaisesRegex(ValueError, "5x5"):
            validate_board([[Piece.EMPTY]])

        board = empty_board()
        board[0][0] = 99
        with self.assertRaisesRegex(ValueError, "invalid board value"):
            validate_board(board)


if __name__ == "__main__":
    unittest.main()
