from __future__ import annotations

import math
import random
import time
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pygame

import config
from ai import choose_move
from rules import (
    BOARD_SIZE,
    CHILD,
    EMPTY,
    INITIAL_CHILDREN,
    TIGER,
    GameState,
    Move,
    count_pieces,
    find_move,
    is_capture,
    row_col,
)

MODES = (
    ("pvp", "双人同屏"),
    ("tiger", "我执老虎 vs 电脑"),
    ("child", "我执小孩 vs 电脑"),
)
LEVELS = (
    ("easy", "简单"),
    ("normal", "普通"),
    ("hard", "困难"),
)
REASONS = {
    "tiger_eats_all": "老虎吃光了所有小孩",
    "child_stuck": "小孩无路可走",
    "tiger_stuck": "老虎被围死了",
    "repetition": "同一局面出现三次",
    "no_capture": "连续 100 个半步没有吃子",
}
MODE_AI = {"pvp": None, "tiger": CHILD, "child": TIGER}
MODE_HUMAN = {"pvp": None, "tiger": TIGER, "child": CHILD}

MOVE_SECONDS = 0.15
THINK_SECONDS = 0.4
FADE_SECONDS = 0.25


@dataclass
class _Animation:
    move: Move
    piece: int
    captured: bool
    started: float
    duration: float = MOVE_SECONDS


class App:
    def __init__(self) -> None:
        self.game = GameState()
        self.mode = "pvp"
        self.ai_side: int | None = None
        self.human_side: int | None = None
        self.level = "normal"
        self.menu_open = True
        self.selected: int | None = None
        self.hovered: int | None = None
        self.thinking = False
        self.running = False
        self.muted = False
        self.initialized = False
        self.fullscreen = True
        self.dirty = True
        self.rng = random.Random()

        self.animation: _Animation | None = None
        self.result_started = 0.0
        self.ai_token = 0
        self.ai_future: tuple[int, Future[Move | None]] | None = None
        self.ai_ready_at = 0.0
        self.executor: ThreadPoolExecutor | None = None
        self.cursor_hand = False

        self.window: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.scene: pygame.Surface | None = None
        self.panel: pygame.Surface | None = None
        self.menu_dim: pygame.Surface | None = None
        self.child_image: pygame.Surface | None = None
        self.tiger_image: pygame.Surface | None = None
        self.small_font: pygame.font.Font | None = None
        self.status_font: pygame.font.Font | None = None
        self.title_font: pygame.font.Font | None = None
        self.winner_font: pygame.font.Font | None = None
        self.sounds: dict[str, pygame.mixer.Sound] = {}
        self.music_ready = False
        self.text_cache: dict[tuple[str, tuple[int, ...], int], pygame.Surface] = {}

        self.view_size = config.WINDOW_SIZE
        self.windowed_size = config.WINDOW_SIZE
        self.scale = 1.0
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.board_origin = config.BOARD_ORIGIN
        self.spacing = float(config.BOARD_SPACING)
        self.piece_size = config.PIECE_SIZE
        self.hit_radius = float(config.HIT_RADIUS)
        self.panel_height = config.TOP_BAR_HEIGHT
        self._layout_rects()

    def _layout_rects(self) -> None:
        scale = self.scale
        width, height = self.view_size
        self.restart_rect = pygame.Rect(
            round(28 * scale), round(22 * scale), round(128 * scale), round(46 * scale)
        )
        self.undo_rect = pygame.Rect(
            round(168 * scale), round(22 * scale), round(88 * scale), round(46 * scale)
        )
        self.sound_rect = pygame.Rect(
            round(268 * scale), round(22 * scale), round(148 * scale), round(46 * scale)
        )
        self.menu_rect = pygame.Rect(
            round(width - 116 * scale), round(22 * scale), round(88 * scale), round(46 * scale)
        )
        self.status_center = (round(width / 2 + 150 * scale), round(45 * scale))
        self.panel_height = max(1, round(config.TOP_BAR_HEIGHT * scale))
        panel_width = 760 * scale
        panel_height = 560 * scale
        panel = pygame.Rect(
            round((width - panel_width) / 2),
            round((height - panel_height) / 2),
            round(panel_width),
            round(panel_height),
        )
        self.menu_panel = panel
        self.mode_buttons = {
            mode: pygame.Rect(
                round(panel.left + 100 * scale),
                round(panel.top + (166 + position * 72) * scale),
                round(560 * scale),
                round(60 * scale),
            )
            for position, (mode, _) in enumerate(MODES)
        }
        self.level_buttons = {
            level: pygame.Rect(
                round(panel.left + (176 + position * 136) * scale),
                round(panel.top + 430 * scale),
                round(128 * scale),
                round(48 * scale),
            )
            for position, (level, _) in enumerate(LEVELS)
        }

    def initialize(self) -> None:
        if self.initialized:
            return

        pygame.init()
        pygame.display.set_caption(config.WINDOW_TITLE)
        if pygame.display.get_driver() != "dummy":
            try:
                desktop_width, desktop_height = pygame.display.get_desktop_sizes()[0]
            except (pygame.error, IndexError):
                desktop_width, desktop_height = config.WINDOW_SIZE
            self.windowed_size = (
                max(640, min(1600, desktop_width - 80)),
                max(360, min(900, desktop_height - 80)),
            )
        self._create_window()
        self.clock = pygame.time.Clock()

        icon = pygame.image.load(str(config.ICON_IMAGE)).convert_alpha()
        pygame.display.set_icon(icon)
        self._relayout()
        self.executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="tiger-ai")
        self._initialize_audio()
        self.initialized = True
        self.dirty = True

    def _create_window(self) -> None:
        driver = pygame.display.get_driver()
        if driver == "dummy":
            self.window = pygame.display.set_mode(config.WINDOW_SIZE)
            return
        try:
            if self.fullscreen:
                size = pygame.display.get_desktop_sizes()[0]
                if size[0] <= 0 or size[1] <= 0:
                    raise pygame.error("unknown desktop size")
                self.window = pygame.display.set_mode(size, pygame.FULLSCREEN)
            else:
                self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)
        except pygame.error:
            self.fullscreen = False
            self.window = pygame.display.set_mode(self.windowed_size, pygame.RESIZABLE)

    def _relayout(self) -> None:
        window = self._require_window()
        width, height = window.get_size()
        self.view_size = (width, height)
        scale = min(width / config.WINDOW_SIZE[0], height / config.WINDOW_SIZE[1])
        self.scale = max(0.25, scale)
        self.offset_x = (width - config.WINDOW_SIZE[0] * self.scale) / 2
        self.offset_y = (height - config.WINDOW_SIZE[1] * self.scale) / 2
        self.board_origin = (
            round(self.offset_x + config.BOARD_ORIGIN[0] * self.scale),
            round(self.offset_y + config.BOARD_ORIGIN[1] * self.scale),
        )
        self.spacing = config.BOARD_SPACING * self.scale
        self.piece_size = (
            max(16, round(config.PIECE_SIZE[0] * self.scale)),
            max(16, round(config.PIECE_SIZE[1] * self.scale)),
        )
        self.hit_radius = config.HIT_RADIUS * self.scale

        self.small_font = pygame.font.Font(str(config.FONT_FILE), max(10, round(24 * self.scale)))
        self.status_font = pygame.font.Font(str(config.FONT_FILE), max(11, round(26 * self.scale)))
        self.title_font = pygame.font.Font(str(config.FONT_FILE), max(20, round(48 * self.scale)))
        self.winner_font = pygame.font.Font(str(config.FONT_FILE), max(28, round(64 * self.scale)))
        self.child_image = self._load_piece(config.CHILD_IMAGE, self.piece_size)
        self.tiger_image = self._load_piece(config.TIGER_IMAGE, self.piece_size)

        self._layout_rects()
        self.scene = self._build_scene()
        self.panel = pygame.Surface((width, self.panel_height), pygame.SRCALPHA)
        self.panel.fill(config.COLORS["panel"])
        self.menu_dim = pygame.Surface((width, height), pygame.SRCALPHA)
        self.menu_dim.fill((20, 24, 36, 170))
        self.text_cache.clear()
        self.dirty = True

    def _toggle_fullscreen(self) -> None:
        if not self.initialized or pygame.display.get_driver() == "dummy":
            return
        self.fullscreen = not self.fullscreen
        self._create_window()
        self._relayout()
        self.dirty = True

    @staticmethod
    def _load_piece(path: Path, box: tuple[int, int]) -> pygame.Surface:
        """Load a piece, trim its transparent border and fit it inside ``box``."""
        image = pygame.image.load(str(path)).convert_alpha()
        bounds = image.get_bounding_rect(min_alpha=1)
        if bounds.width == 0 or bounds.height == 0:
            raise ValueError(f"image has no visible pixels: {path}")
        content = image.subsurface(bounds).copy()
        scale = min(box[0] / bounds.width, box[1] / bounds.height)
        size = (max(1, round(bounds.width * scale)), max(1, round(bounds.height * scale)))
        return pygame.transform.smoothscale(content, size)

    @staticmethod
    def _load_cover(path: Path, size: tuple[int, int]) -> pygame.Surface:
        image = pygame.image.load(str(path)).convert()
        scale = max(size[0] / image.get_width(), size[1] / image.get_height())
        scaled_size = (
            max(size[0], round(image.get_width() * scale)),
            max(size[1], round(image.get_height() * scale)),
        )
        scaled = pygame.transform.smoothscale(image, scaled_size)
        offset = (
            (scaled.get_width() - size[0]) // 2,
            (scaled.get_height() - size[1]) // 2,
        )
        result = pygame.Surface(size)
        result.blit(scaled, (-offset[0], -offset[1]))
        return result

    def _build_scene(self) -> pygame.Surface:
        background = self._load_cover(config.BACKGROUND_IMAGE, self.view_size)
        wash = pygame.Surface(self.view_size, pygame.SRCALPHA)
        wash.fill((255, 255, 255, 42))
        background.blit(wash, (0, 0))

        origin_x, origin_y = self.board_origin
        spacing = self.spacing
        extent = spacing * (BOARD_SIZE - 1)
        line_width = max(1, round(config.BOARD_LINE_WIDTH * self.scale))
        dot_radius = max(2, round(8 * self.scale))
        for index in range(BOARD_SIZE):
            offset = round(index * spacing)
            pygame.draw.line(
                background,
                config.COLORS["board"],
                (origin_x, origin_y + offset),
                (round(origin_x + extent), origin_y + offset),
                line_width,
            )
            pygame.draw.line(
                background,
                config.COLORS["board"],
                (origin_x + offset, origin_y),
                (origin_x + offset, round(origin_y + extent)),
                line_width,
            )
        for cell in range(BOARD_SIZE * BOARD_SIZE):
            pygame.draw.circle(
                background, config.COLORS["board"], self.cell_center(cell), dot_radius
            )
        return background

    def _initialize_audio(self) -> None:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            pygame.mixer.music.load(str(config.BACKGROUND_MUSIC))
            pygame.mixer.music.set_volume(config.BACKGROUND_VOLUME)
            self.sounds = {
                "move": pygame.mixer.Sound(str(config.MOVE_SOUND)),
                "win": pygame.mixer.Sound(str(config.WIN_SOUND)),
            }
            for sound in self.sounds.values():
                sound.set_volume(config.EFFECT_VOLUME)
            self.music_ready = True
        except (pygame.error, OSError):
            self.sounds = {}
            self.music_ready = False

    def _require_window(self) -> pygame.Surface:
        if self.window is None:
            raise RuntimeError("App.initialize() must be called before rendering")
        return self.window

    def _require_font(self, font: pygame.font.Font | None) -> pygame.font.Font:
        if font is None:
            raise RuntimeError("App.initialize() must be called before drawing text")
        return font

    def run(self, max_frames: int | None = None) -> None:
        """Run the loop. ``max_frames`` is a test hook for a smoke run."""
        self.initialize()
        self.running = True
        self._sync_music()
        self._draw_and_flip()
        if self.ai_side is not None and self.ai_side == self.game.player:
            self._start_ai()

        clock = self.clock
        if clock is None:
            raise RuntimeError("App.initialize() must be called before run()")
        frame_count = 0
        try:
            while self.running:
                for event in pygame.event.get():
                    self.handle_event(event)
                self._tick()
                if self.dirty:
                    self._draw_and_flip()
                clock.tick(config.FPS)
                frame_count += 1
                if max_frames is not None and frame_count >= max_frames:
                    self.running = False
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        self._cancel_ai()
        if self.executor is not None:
            self.executor.shutdown(wait=False, cancel_futures=True)
            self.executor = None
        if pygame.mixer.get_init() is not None:
            pygame.mixer.music.stop()
        for sound in self.sounds.values():
            sound.stop()
        self.sounds = {}
        pygame.quit()
        self.initialized = False

    def _tick(self) -> None:
        now = time.monotonic()
        if self.animation is not None:
            self.dirty = True
            if now >= self.animation.started + self.animation.duration:
                self.animation = None
                self._after_animation()
        if self.thinking:
            self.dirty = True
            self._poll_ai(now)
        if (
            self.game.is_over
            and self.animation is None
            and self.result_started
            and now - self.result_started < FADE_SECONDS
        ):
            self.dirty = True
        self._update_cursor()

    def _after_animation(self) -> None:
        self._play_sound("move")
        if self.game.is_over:
            self._sync_music()
            self._play_sound("win")
            self.result_started = time.monotonic()
            self.dirty = True
            return
        if self.ai_side is not None and self.game.player == self.ai_side:
            self._start_ai()

    def _start_ai(self) -> None:
        if (
            self.executor is None
            or self.thinking
            or self.animation is not None
            or self.menu_open
            or self.game.is_over
            or self.ai_side is None
        ):
            return
        if self.game.player != self.ai_side:
            return

        snapshot = GameState(
            board=self.game.board,
            player=self.game.player,
            move_count=self.game.move_count,
            non_capture=self.game.non_capture,
        )
        snapshot.positions = dict(self.game.positions)
        self.ai_token += 1
        token = self.ai_token
        self.thinking = True
        self.ai_future = (token, self.executor.submit(choose_move, snapshot, self.level, self.rng))
        self.ai_ready_at = time.monotonic() + THINK_SECONDS
        self.dirty = True

    def _poll_ai(self, now: float) -> None:
        if self.ai_future is None:
            self.thinking = False
            return
        token, future = self.ai_future
        if token != self.ai_token:
            self.ai_future = None
            self.thinking = False
            return
        if not future.done() or now < self.ai_ready_at:
            return

        self.ai_future = None
        self.thinking = False
        try:
            move = future.result()
        except Exception:
            move = None
        if move is None or self.game.is_over or self.game.player != self.ai_side:
            legal = self.game.legal_moves()
            move = legal[0] if legal else None
        if move is not None and not self.game.is_over and self.game.player == self.ai_side:
            self._apply_move(move)
        else:
            self.dirty = True

    def _cancel_ai(self) -> None:
        self.ai_token += 1
        self.ai_future = None
        self.thinking = False
        self.ai_ready_at = 0.0

    def _apply_move(self, move: Move) -> None:
        self.game.play(move)
        self.animation = _Animation(
            move=move,
            piece=self.game.board[move[1]],
            captured=is_capture(move),
            started=time.monotonic(),
        )
        self.selected = None
        self.hovered = None
        self.dirty = True

    def start_mode(self, mode: str) -> None:
        self._cancel_ai()
        self.animation = None
        self.result_started = 0.0
        self.mode = mode
        self.ai_side = MODE_AI[mode]
        self.human_side = MODE_HUMAN[mode]
        self.game = GameState()
        self.menu_open = False
        self.selected = None
        self.hovered = None
        self._stop_sound("win")
        self._sync_music()
        self.dirty = True
        if self.initialized and self.ai_side == self.game.player:
            self._start_ai()

    def restart(self) -> None:
        self._cancel_ai()
        self.animation = None
        self.result_started = 0.0
        self.game = GameState()
        self.selected = None
        self.hovered = None
        self._stop_sound("win")
        self._sync_music()
        self.dirty = True
        if self.initialized and self.ai_side == self.game.player:
            self._start_ai()

    def _can_undo(self) -> bool:
        if self.menu_open or self.thinking or self.animation is not None or not self.game.history:
            return False
        if self.ai_side is None:
            return True
        minimum = 1 if self.ai_side == TIGER else 0
        return self.game.move_count > minimum

    def undo(self) -> None:
        if not self._can_undo():
            return
        self._cancel_ai()
        self.animation = None
        self.result_started = 0.0
        self.game.undo()
        if self.ai_side is not None and self.game.player != self.human_side:
            self.game.undo()
        self.selected = None
        self.hovered = None
        self._stop_sound("win")
        self._sync_music()
        self.dirty = True
        if self.initialized and self.ai_side == self.game.player:
            self._start_ai()

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        if pygame.mixer.get_init() is not None:
            if self.muted:
                pygame.mixer.pause()
            else:
                pygame.mixer.unpause()
                if self.music_ready and not self.game.is_over and not pygame.mixer.music.get_busy():
                    pygame.mixer.music.play(-1)
        self.dirty = True

    def _sync_music(self) -> None:
        if not self.music_ready or pygame.mixer.get_init() is None:
            return
        if self.game.is_over or self.muted:
            pygame.mixer.music.stop()
        elif not pygame.mixer.music.get_busy():
            pygame.mixer.music.play(-1)

    def _play_sound(self, name: str) -> None:
        if self.muted:
            return
        sound = self.sounds.get(name)
        if sound is not None:
            sound.play()

    def _stop_sound(self, name: str) -> None:
        sound = self.sounds.get(name)
        if sound is not None:
            sound.stop()

    def cell_center(self, cell: int) -> tuple[int, int]:
        row, column = row_col(cell)
        return (
            round(self.board_origin[0] + column * self.spacing),
            round(self.board_origin[1] + row * self.spacing),
        )

    def position_to_cell(self, position: tuple[int, int]) -> int | None:
        """Map a window point to the nearest cell centre within the hit radius."""
        x, y = position
        origin_x, origin_y = self.board_origin
        spacing = self.spacing
        column = math.floor((x - origin_x) / spacing + 0.5)
        row = math.floor((y - origin_y) / spacing + 0.5)
        if not (0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE):
            return None

        center_x = origin_x + column * spacing
        center_y = origin_y + row * spacing
        if (x - center_x) ** 2 + (y - center_y) ** 2 > self.hit_radius**2:
            return None
        return row * BOARD_SIZE + column

    def status_text(self) -> str:
        if self.menu_open:
            return "选择模式开始"
        if self.game.winner == TIGER:
            return "对局结束   老虎胜"
        if self.game.winner == CHILD:
            return "对局结束   小孩胜"
        if self.game.draw:
            return "对局结束   平局"
        if self.thinking:
            dots = "." * (1 + int(time.monotonic() * 4) % 3)
            return "电脑思考中" + dots
        side = "老虎" if self.game.player == TIGER else "小孩"
        children = count_pieces(self.game.board, CHILD)
        return f"第 {self.game.move_count + 1} 手   {side}走   小孩 {children}/{INITIAL_CHILDREN}"

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            self._handle_key(event.key)
        elif event.type == pygame.MOUSEMOTION:
            self.dirty = True
            if not self.menu_open:
                self.hovered = self.position_to_cell(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.menu_open:
                self._handle_menu_click(event.pos)
            else:
                self._handle_click(event.pos)
        elif event.type == pygame.VIDEORESIZE and not self.fullscreen:
            size = (max(640, event.w), max(360, event.h))
            self.windowed_size = size
            if self.window is None or self.window.get_size() != size:
                self.window = pygame.display.set_mode(size, pygame.RESIZABLE)
            self._relayout()

    def _handle_key(self, key: int) -> None:
        if key == pygame.K_F11:
            self._toggle_fullscreen()
            return
        if key == pygame.K_q:
            self.running = False
            return
        if key == pygame.K_ESCAPE:
            if self.menu_open:
                self.menu_open = False
            else:
                self._toggle_fullscreen()
            self.dirty = True
            return
        if key == pygame.K_m:
            self.toggle_mute()
            return
        if self.thinking or self.animation is not None:
            return
        if key == pygame.K_r and not self.menu_open:
            self.restart()
        elif key == pygame.K_u:
            self.undo()

    def _handle_menu_click(self, position: tuple[int, int]) -> None:
        if self.menu_rect.collidepoint(position):
            self.menu_open = False
            self.dirty = True
            return
        for mode, rect in self.mode_buttons.items():
            if rect.collidepoint(position):
                self.start_mode(mode)
                return
        for level, rect in self.level_buttons.items():
            if rect.collidepoint(position):
                self.level = level
                self.dirty = True
                return

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.sound_rect.collidepoint(position):
            self.toggle_mute()
            return
        if self.thinking or self.animation is not None:
            return
        if self.restart_rect.collidepoint(position):
            self.restart()
            return
        if self.undo_rect.collidepoint(position):
            self.undo()
            return
        if self.menu_rect.collidepoint(position):
            self.menu_open = True
            self.selected = None
            self.dirty = True
            return
        if self.game.is_over:
            return
        if self.ai_side is not None and self.game.player == self.ai_side:
            return

        cell = self.position_to_cell(position)
        if cell is None:
            self.selected = None
            self.dirty = True
            return

        if self.selected is None:
            if self.game.board[cell] == self.game.player:
                self.selected = cell
                self.dirty = True
            return
        if cell == self.selected:
            self.selected = None
            self.dirty = True
            return
        if self.game.board[cell] == self.game.player:
            self.selected = cell
            self.dirty = True
            return

        move = find_move(self.game.board, self.selected, cell)
        if move is None:
            return
        self._apply_move(move)

    def _update_cursor(self) -> None:
        if not self.initialized or pygame.display.get_driver() == "dummy":
            return
        position = pygame.mouse.get_pos()
        if self.menu_open:
            hand = self.menu_rect.collidepoint(position)
            if not hand:
                hand = any(rect.collidepoint(position) for rect in self.mode_buttons.values())
            if not hand:
                hand = any(rect.collidepoint(position) for rect in self.level_buttons.values())
        else:
            hand = self.sound_rect.collidepoint(position)
            if not hand and not (self.thinking or self.animation is not None):
                hand = self.restart_rect.collidepoint(position) or self.menu_rect.collidepoint(
                    position
                )
            if not hand and self._can_undo():
                hand = self.undo_rect.collidepoint(position)
            if not hand and not (self.game.is_over or self.thinking or self.animation is not None):
                cell = self.position_to_cell(position)
                hand = cell is not None and self.game.board[cell] == self.game.player
        if hand != self.cursor_hand:
            self.cursor_hand = hand
            cursor = pygame.SYSTEM_CURSOR_HAND if hand else pygame.SYSTEM_CURSOR_ARROW
            pygame.mouse.set_cursor(cursor)

    def _draw_and_flip(self) -> None:
        self.render()
        pygame.display.flip()
        self.dirty = False

    def render(self) -> None:
        window = self._require_window()
        scene = self.scene
        if scene is None:
            raise RuntimeError("App.initialize() must be called before rendering")
        window.blit(scene, (0, 0))

        self._draw_top_bar()
        self._draw_pieces()
        if self.animation is not None:
            self._draw_animation()
        else:
            self._draw_last_move()
            self._draw_move_hints()
        if self.game.is_over and self.animation is None:
            self._draw_winner_band()
        if self.menu_open:
            self._draw_menu()

    def _draw_top_bar(self) -> None:
        window = self._require_window()
        panel = self.panel
        if panel is None:
            raise RuntimeError("App.initialize() must be called before rendering")
        window.blit(panel, (0, 0))
        locked = self.thinking or self.animation is not None
        self._draw_button(self.restart_rect, "重新开始", enabled=not locked)
        self._draw_button(self.undo_rect, "悔棋", enabled=self._can_undo())
        self._draw_button(self.sound_rect, "声音 开" if not self.muted else "声音 关")
        self._draw_button(self.menu_rect, "菜单", enabled=not locked)

        surface = self._text(
            self.status_text(), config.COLORS["ink"], self._require_font(self.status_font)
        )
        rect = surface.get_rect(center=self.status_center)
        window.blit(surface, rect)
        if not self.menu_open and not self.game.is_over and not self.thinking:
            color = config.COLORS["tiger"] if self.game.player == TIGER else config.COLORS["child"]
            pygame.draw.circle(
                window,
                color,
                (rect.left - round(24 * self.scale), self.status_center[1]),
                max(3, round(8 * self.scale)),
            )

    def _draw_button(self, rect: pygame.Rect, label: str, enabled: bool = True) -> None:
        window = self._require_window()
        hovered = enabled and rect.collidepoint(pygame.mouse.get_pos())
        if not enabled:
            fill = config.COLORS["button_disabled"]
            border = config.COLORS["button_disabled_border"]
            color = config.COLORS["muted_text"]
        else:
            fill = config.COLORS["button_hover"] if hovered else config.COLORS["button"]
            border = config.COLORS["button_border"]
            color = config.COLORS["ink"]
        radius = max(2, round(6 * self.scale))
        pygame.draw.rect(window, fill, rect, border_radius=radius)
        pygame.draw.rect(
            window, border, rect, width=max(1, round(2 * self.scale)), border_radius=radius
        )
        self._draw_text(label, rect.center, color, self.small_font)

    def _draw_menu_button(
        self,
        rect: pygame.Rect,
        label: str,
        primary: bool = False,
        active: bool = False,
    ) -> None:
        window = self._require_window()
        hovered = rect.collidepoint(pygame.mouse.get_pos())
        if primary:
            fill = config.COLORS["button_hover"] if hovered else config.COLORS["button"]
            color = config.COLORS["ink"]
        elif active:
            fill = config.COLORS["legal"]
            color = config.COLORS["white"]
        else:
            fill = config.COLORS["menu_button_hover"] if hovered else config.COLORS["menu_button"]
            color = config.COLORS["white"]
        radius = max(2, round(6 * self.scale))
        pygame.draw.rect(window, fill, rect, border_radius=radius)
        pygame.draw.rect(
            window,
            config.COLORS["button_border"],
            rect,
            width=max(1, round(2 * self.scale)),
            border_radius=radius,
        )
        self._draw_text(label, rect.center, color, self.small_font)

    def _draw_pieces(self) -> None:
        window = self._require_window()
        child_image = self.child_image
        tiger_image = self.tiger_image
        if child_image is None or tiger_image is None:
            raise RuntimeError("App.initialize() must be called before rendering")
        animation = self.animation
        select_radius = max(8, round(60 * self.scale))
        hover_radius = max(6, round(52 * self.scale))
        select_width = max(2, round(5 * self.scale))
        hover_width = max(1, round(3 * self.scale))
        for cell, piece in enumerate(self.game.board):
            if piece == EMPTY:
                continue
            if animation is not None and cell == animation.move[1]:
                continue
            image = child_image if piece == CHILD else tiger_image
            center = self.cell_center(cell)
            window.blit(image, image.get_rect(center=center))
            if animation is not None:
                continue
            if cell == self.selected:
                pygame.draw.circle(
                    window, config.COLORS["select"], center, select_radius, width=select_width
                )
            elif (
                cell == self.hovered
                and piece == self.game.player
                and not self.game.is_over
                and not self.thinking
            ):
                pygame.draw.circle(
                    window,
                    config.COLORS["button_border"],
                    center,
                    hover_radius,
                    width=hover_width,
                )

    def _draw_animation(self) -> None:
        animation = self.animation
        if animation is None:
            return
        window = self._require_window()
        elapsed = time.monotonic() - animation.started
        t = min(1.0, max(0.0, elapsed / animation.duration))
        eased = t * t * (3.0 - 2.0 * t)
        start = self.cell_center(animation.move[0])
        end = self.cell_center(animation.move[1])

        if animation.captured and self.child_image is not None:
            fading = self.child_image.copy()
            fading.set_alpha(int(255 * (1.0 - t)))
            window.blit(fading, fading.get_rect(center=end))

        image = self.tiger_image if animation.piece == TIGER else self.child_image
        if image is None:
            return
        x = start[0] + (end[0] - start[0]) * eased
        y = start[1] + (end[1] - start[1]) * eased
        window.blit(image, image.get_rect(center=(round(x), round(y))))

    def _draw_last_move(self) -> None:
        move = self.game.last_move
        if move is None:
            return
        window = self._require_window()
        start, end = move
        pygame.draw.circle(
            window,
            config.COLORS["last"],
            self.cell_center(start),
            max(2, round(10 * self.scale)),
        )
        pygame.draw.circle(
            window,
            config.COLORS["last"],
            self.cell_center(end),
            max(8, round(60 * self.scale)),
            width=max(1, round(3 * self.scale)),
        )

    def _draw_move_hints(self) -> None:
        if self.selected is None:
            return
        window = self._require_window()
        ring = max(8, round(60 * self.scale))
        ring_width = max(2, round(6 * self.scale))
        dot = max(2, round(12 * self.scale))
        for move in self.game.moves_from(self.selected):
            end = move[1]
            center = self.cell_center(end)
            if is_capture(move):
                pygame.draw.circle(window, config.COLORS["capture"], center, ring, width=ring_width)
            else:
                pygame.draw.circle(window, config.COLORS["legal"], center, dot)

    def _draw_winner_band(self) -> None:
        window = self._require_window()
        now = time.monotonic()
        if not self.result_started:
            self.result_started = now
        fade = min(1.0, (now - self.result_started) / FADE_SECONDS)

        height = max(80, round(config.WINNER_BAND_HEIGHT * self.scale))
        width = self.view_size[0]
        band = pygame.Surface((width, height), pygame.SRCALPHA)
        band.fill(config.COLORS["overlay"])
        if self.game.draw:
            label = "平局"
        elif self.game.winner == TIGER:
            label = "老虎胜利"
        else:
            label = "小孩胜利"
        reason = REASONS.get(self.game.end_reason or "", "")
        center_x = width // 2
        self._text_at(
            band,
            label,
            (center_x, round(70 * self.scale)),
            config.COLORS["white"],
            self.winner_font,
        )
        if reason:
            self._text_at(
                band,
                reason,
                (center_x, round(150 * self.scale)),
                config.COLORS["white"],
                self.small_font,
            )
        self._text_at(
            band,
            "按 R 再来一局",
            (center_x, round(200 * self.scale)),
            config.COLORS["white"],
            self.small_font,
        )
        band.set_alpha(int(255 * fade))
        window.blit(band, (0, (self.view_size[1] - height) // 2))

    def _draw_menu(self) -> None:
        window = self._require_window()
        dim = self.menu_dim
        if dim is not None:
            window.blit(dim, (0, 0))

        scale = self.scale
        panel = self.menu_panel
        pygame.draw.rect(
            window, config.COLORS["menu_panel"], panel, border_radius=max(4, round(12 * scale))
        )
        pygame.draw.rect(
            window,
            config.COLORS["button_border"],
            panel,
            width=max(1, round(2 * scale)),
            border_radius=max(4, round(12 * scale)),
        )
        self._draw_text(
            "老虎吃小孩",
            (panel.centerx, round(panel.top + 65 * scale)),
            config.COLORS["white"],
            self.title_font,
        )
        self._draw_text(
            "双人同屏，或者和电脑下",
            (panel.centerx, round(panel.top + 122 * scale)),
            config.COLORS["muted_text"],
            self.small_font,
        )
        for mode, label in MODES:
            self._draw_menu_button(self.mode_buttons[mode], label, primary=True)
        self._draw_text(
            "电脑难度",
            (panel.centerx, round(panel.top + 400 * scale)),
            config.COLORS["muted_text"],
            self.small_font,
        )
        for level, label in LEVELS:
            self._draw_menu_button(self.level_buttons[level], label, active=level == self.level)
        self._draw_text(
            "点击模式开始    Esc 返回    Q 退出",
            (panel.centerx, round(panel.top + 500 * scale)),
            config.COLORS["muted_text"],
            self.small_font,
        )
        self._draw_text(
            "R 重开   U 悔棋   M 静音   F11 全屏",
            (panel.centerx, round(panel.top + 535 * scale)),
            config.COLORS["muted_text"],
            self.small_font,
        )

    def _draw_text(
        self,
        text: str,
        center: tuple[int, int],
        color: tuple[int, ...],
        font: pygame.font.Font | None,
    ) -> None:
        self._text_at(self._require_window(), text, center, color, font)

    def _text_at(
        self,
        surface: pygame.Surface,
        text: str,
        center: tuple[int, int],
        color: tuple[int, ...],
        font: pygame.font.Font | None,
    ) -> None:
        rendered = self._text(text, color, self._require_font(font))
        surface.blit(rendered, rendered.get_rect(center=center))

    def _text(self, text: str, color: tuple[int, ...], font: pygame.font.Font) -> pygame.Surface:
        key = (text, color, font.get_height())
        surface = self.text_cache.get(key)
        if surface is None:
            surface = font.render(text, True, color)
            if len(self.text_cache) > 512:
                self.text_cache.clear()
            self.text_cache[key] = surface
        return surface


def main() -> None:
    App().run()


if __name__ == "__main__":
    main()
