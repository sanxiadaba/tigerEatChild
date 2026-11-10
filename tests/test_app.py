import os
import time
import unittest

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
os.environ.setdefault("PYGAME_HIDE_SUPPORT_PROMPT", "1")

import pygame

import config
from app import App
from rules import CHILD, EMPTY, TIGER, GameState

PIECES = {".": EMPTY, "C": CHILD, "T": TIGER}


def board(text: str):
    flat = "".join(text.split())
    assert len(flat) == 25, len(flat)
    return bytes(PIECES[char] for char in flat)


def pump(app: App, predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        app._tick()
        time.sleep(0.01)
    return predicate()


class AppTests(unittest.TestCase):
    def tearDown(self):
        if pygame.get_init():
            pygame.quit()

    def test_position_mapping(self):
        origin = config.BOARD_ORIGIN
        spacing = config.BOARD_SPACING
        radius = config.HIT_RADIUS

        self.assertEqual(App.position_to_cell(origin), 0)
        self.assertEqual(App.position_to_cell(App.cell_center(24)), 24)

        center = App.cell_center(22)
        self.assertEqual(App.position_to_cell((center[0] + radius - 1, center[1])), 22)
        self.assertIsNone(App.position_to_cell((center[0] + radius + 1, center[1])))
        self.assertIsNone(
            App.position_to_cell((origin[0] + spacing // 2, origin[1] + spacing // 2))
        )
        self.assertIsNone(App.position_to_cell((0, 0)))
        self.assertIsNone(
            App.position_to_cell((config.WINDOW_SIZE[0] - 1, config.WINDOW_SIZE[1] - 1))
        )
        self.assertIsNone(App.position_to_cell((800, config.TOP_BAR_HEIGHT - 1)))

    def test_piece_images_fill_the_box(self):
        app = App()
        app.initialize()
        try:
            for image in (app.child_image, app.tiger_image):
                self.assertIsNotNone(image)
                width, height = image.get_size()
                self.assertLessEqual(width, config.PIECE_SIZE[0])
                self.assertLessEqual(height, config.PIECE_SIZE[1])
                self.assertGreaterEqual(min(width, height), 0.7 * min(config.PIECE_SIZE))
        finally:
            app.shutdown()

    def test_clicks_select_and_move(self):
        app = App()
        app.initialize()
        try:
            app.start_mode("pvp")

            app._handle_click(App.cell_center(20))
            self.assertEqual(app.selected, 20)

            app._handle_click(App.cell_center(15))
            self.assertIsNone(app.selected)
            self.assertEqual(app.game.move_count, 1)
            self.assertEqual(app.game.player, CHILD)
            self.assertIsNotNone(app.animation)
        finally:
            app.shutdown()

    def test_dead_space_clears_the_selection(self):
        app = App()
        app.initialize()
        try:
            app.start_mode("pvp")
            app._handle_click(App.cell_center(20))
            self.assertEqual(app.selected, 20)

            app._handle_click((0, 0))

            self.assertIsNone(app.selected)
        finally:
            app.shutdown()

    def test_undo_restores_the_game(self):
        app = App()
        app.initialize()
        try:
            app.start_mode("pvp")
            app.game.play((20, 15))

            app.undo()

            self.assertEqual(app.game.move_count, 0)
            self.assertEqual(app.game.player, TIGER)
            self.assertIsNone(app.game.last_move)
            self.assertFalse(app.undo())
        finally:
            app.shutdown()

    def test_restart_keeps_the_mode(self):
        app = App()
        app.initialize()
        try:
            app.start_mode("pvp")
            app.game.play((20, 15))

            app.restart()

            self.assertEqual(app.mode, "pvp")
            self.assertFalse(app.menu_open)
            self.assertEqual(app.game.move_count, 0)
            self.assertEqual(app.game.player, TIGER)
        finally:
            app.shutdown()

    def test_status_text(self):
        app = App()
        app.start_mode("pvp")
        self.assertIn("老虎走", app.status_text())

        app.game = GameState(board=board("..... ..... ..... ..... T.T.T"))
        self.assertIn("老虎胜", app.status_text())

        app.menu_open = True
        self.assertIn("选择模式", app.status_text())

    def test_menu_modes(self):
        app = App()
        app.initialize()
        try:
            app.start_mode("tiger")
            self.assertEqual(app.ai_side, CHILD)
            self.assertEqual(app.human_side, TIGER)
            self.assertEqual(app.game.player, TIGER)
            self.assertFalse(app.menu_open)

            app.start_mode("child")
            self.assertTrue(pump(app, lambda: app.game.move_count == 1))
            self.assertEqual(app.ai_side, TIGER)
            self.assertEqual(app.human_side, CHILD)
            self.assertEqual(app.game.player, CHILD)
            self.assertFalse(app.game.is_over)
        finally:
            app.shutdown()

    def test_ai_move_is_delayed_and_animated(self):
        app = App()
        app.initialize()
        try:
            app.start_mode("child")
            started = time.monotonic()
            self.assertTrue(pump(app, lambda: app.game.move_count == 1))
            self.assertGreaterEqual(time.monotonic() - started, 0.35)
            self.assertIsNotNone(app.animation)
        finally:
            app.shutdown()

    def test_mute_toggles(self):
        app = App()
        self.assertFalse(app.muted)
        app.toggle_mute()
        self.assertTrue(app.muted)
        app.toggle_mute()
        self.assertFalse(app.muted)

    def test_render_handles_every_state(self):
        app = App()
        app.initialize()
        try:
            app.render()

            app.start_mode("pvp")
            app._handle_click(App.cell_center(20))
            app.render()
            app._handle_click(App.cell_center(15))
            app.render()
            self.assertTrue(pump(app, lambda: app.animation is None))

            app.animation = None
            app.game = GameState(board=board("..... ..... ..... ..... T.T.T"))
            app.result_started = 0.0
            app.render()

            app.menu_open = True
            app.render()
        finally:
            app.shutdown()

    def test_headless_smoke_run(self):
        app = App()

        app.run(max_frames=3)

        self.assertFalse(app.initialized)
        self.assertFalse(pygame.get_init())


if __name__ == "__main__":
    unittest.main()
