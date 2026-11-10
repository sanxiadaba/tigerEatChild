import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

import constant
from display_game import Board
from game_logic import GameState, Piece, Player


def empty_board():
    return [[Piece.EMPTY for _ in range(5)] for _ in range(5)]


class DisplayGameTests(unittest.TestCase):
    def tearDown(self):
        if pygame.get_init():
            pygame.quit()

    def test_position_mapping_stays_inside_board(self):
        self.assertEqual(Board.position_to_cell(constant.BOARD_ORIGIN), (0, 0))
        self.assertEqual(Board.position_to_cell(Board.cell_center((4, 4))), (4, 4))
        self.assertEqual(Board.position_to_cell((400, 645)), (4, 2))
        self.assertIsNone(Board.position_to_cell((400, 649)))
        self.assertIsNone(Board.position_to_cell((400, 700)))
        self.assertIsNone(Board.position_to_cell((0, 0)))

    def test_position_mapping_ignores_space_outside_the_board(self):
        # 60 px to the left/right of the outer columns used to hit the edge
        # pieces; the hit radius is 48 px, so these clicks are dead.
        self.assertIsNone(Board.position_to_cell((100, 300)))
        self.assertIsNone(Board.position_to_cell((700, 300)))
        # The top bar overlaps the row-0 cell box; it must not select a piece.
        self.assertIsNone(Board.position_to_cell((400, 60)))
        # Exactly halfway between two pieces is a dead zone, not a coin flip.
        self.assertIsNone(Board.position_to_cell((220, 300)))

    def test_piece_images_are_visually_consistent(self):
        board = Board()
        board.initialize()
        try:
            images = board.child_images + board.tiger_images
            self.assertTrue(images)
            smallest = min(min(image.get_size()) for image in images)
            largest = max(max(image.get_size()) for image in images)
            for image in images:
                self.assertLessEqual(
                    image.get_width(),
                    constant.PIECE_SIZE[0],
                    "piece image exceeds the configured box",
                )
                self.assertLessEqual(
                    image.get_height(),
                    constant.PIECE_SIZE[1],
                    "piece image exceeds the configured box",
                )
            # Untrimmed canvases made children ~50 px wide next to a ~92 px
            # tiger; after trimming, every piece fills most of the box.
            self.assertGreaterEqual(smallest, 0.7 * min(constant.PIECE_SIZE))
            self.assertLessEqual(largest, max(constant.PIECE_SIZE))
        finally:
            board.shutdown()

    def test_clicks_select_piece_and_apply_legal_move(self):
        board = Board()
        board.initialize()
        try:
            board._handle_click(Board.cell_center((2, 0)))
            self.assertIsNone(board.selected)

            board._handle_click(Board.cell_center((4, 0)))
            self.assertEqual(board.selected, (4, 0))
            board._handle_click(Board.cell_center((3, 0)))
            self.assertIsNone(board.selected)
            self.assertEqual(board.game.current_player, Player.CHILD)
        finally:
            board.shutdown()

    def test_click_on_dead_space_clears_the_selection(self):
        board = Board()
        board.initialize()
        try:
            board._handle_click(Board.cell_center((4, 0)))
            self.assertEqual(board.selected, (4, 0))
            board._handle_click((0, 0))
            self.assertIsNone(board.selected)
        finally:
            board.shutdown()

    def test_restart_restores_initial_turn(self):
        board = Board()
        board.game.play((4, 0), (3, 0))

        board.restart()

        self.assertEqual(board.game.current_player, Player.TIGER)
        self.assertEqual(board.game.move_count, 0)
        self.assertFalse(board.game.is_draw)

    def test_status_text_switches_to_game_over(self):
        board = Board()
        self.assertIn("老虎回合", board.status_text())

        # A board without children is an immediate tiger win.
        board.game = GameState(board=empty_board())

        self.assertTrue(board.game.is_over)
        self.assertIn("对局结束", board.status_text())
        self.assertNotIn("回合", board.status_text())

    def test_three_frame_headless_smoke_run(self):
        board = Board()

        board.run(max_frames=3)

        self.assertFalse(board.initialized)
        self.assertFalse(pygame.get_init())


if __name__ == "__main__":
    unittest.main()
