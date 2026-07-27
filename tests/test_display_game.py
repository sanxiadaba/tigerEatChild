import os
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

import constant
from display_game import Board
from game_logic import Player


class DisplayGameTests(unittest.TestCase):
    def tearDown(self):
        if pygame.get_init():
            pygame.quit()

    def test_position_mapping_stays_inside_board(self):
        self.assertEqual(Board.position_to_cell(constant.BOARD_ORIGIN), (0, 0))
        self.assertEqual(Board.position_to_cell(Board.cell_center((4, 4))), (4, 4))
        self.assertEqual(Board.position_to_cell((400, 649)), (4, 2))
        self.assertIsNone(Board.position_to_cell((400, 700)))
        self.assertIsNone(Board.position_to_cell((0, 0)))

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

    def test_restart_restores_initial_turn(self):
        board = Board()
        board.game.play((4, 0), (3, 0))

        board.restart()

        self.assertEqual(board.game.current_player, Player.TIGER)
        self.assertEqual(board.game.move_count, 0)
        self.assertFalse(board.game.is_draw)

    def test_three_frame_headless_smoke_run(self):
        board = Board()

        board.run(max_frames=3)

        self.assertFalse(board.initialized)
        self.assertFalse(pygame.get_init())


if __name__ == "__main__":
    unittest.main()
