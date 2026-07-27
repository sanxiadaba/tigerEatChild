from __future__ import annotations

from pathlib import Path

import pygame

import constant
from game_logic import (
    BOARD_SIZE,
    GameState,
    Piece,
    Player,
    Position,
    count_pieces,
)


class Board:
    def __init__(self) -> None:
        self.game = GameState()
        self.selected: Position | None = None
        self.hovered: Position | None = None
        self.running = False
        self.muted = False
        self.initialized = False

        self.window: pygame.Surface | None = None
        self.clock: pygame.time.Clock | None = None
        self.background: pygame.Surface | None = None
        self.child_images: tuple[pygame.Surface, ...] = ()
        self.tiger_images: tuple[pygame.Surface, ...] = ()
        self.font: pygame.font.Font | None = None
        self.small_font: pygame.font.Font | None = None
        self.winner_font: pygame.font.Font | None = None
        self.sounds: dict[str, pygame.mixer.Sound] = {}

        self.restart_button = pygame.Rect(20, 18, 112, 40)
        self.sound_button = pygame.Rect(668, 18, 112, 40)

    def initialize(self) -> None:
        if self.initialized:
            return

        pygame.init()
        pygame.display.set_caption(constant.WINDOW_TITLE)
        self.window = pygame.display.set_mode(constant.WINDOW_SIZE)
        self.clock = pygame.time.Clock()

        icon = pygame.image.load(str(constant.ICON_IMAGE))
        pygame.display.set_icon(icon)
        self.background = self._load_cover_image(
            constant.BACKGROUND_IMAGE, constant.WINDOW_SIZE
        )
        self.child_images = tuple(
            self._load_scaled_image(path, constant.PIECE_SIZE)
            for path in constant.CHILD_IMAGES
        )
        self.tiger_images = tuple(
            self._load_scaled_image(path, constant.PIECE_SIZE)
            for path in constant.TIGER_IMAGES
        )
        self.font = pygame.font.Font(str(constant.FONT_FILE), 25)
        self.small_font = pygame.font.Font(str(constant.FONT_FILE), 19)
        self.winner_font = pygame.font.Font(str(constant.FONT_FILE), 48)
        self._initialize_audio()
        self.initialized = True

    @staticmethod
    def _load_scaled_image(path: Path, size: tuple[int, int]) -> pygame.Surface:
        image = pygame.image.load(str(path)).convert_alpha()
        return pygame.transform.smoothscale(image, size)

    @staticmethod
    def _load_cover_image(path: Path, size: tuple[int, int]) -> pygame.Surface:
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

    def _initialize_audio(self) -> None:
        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init()
            self.sounds = {
                "background": pygame.mixer.Sound(str(constant.BACKGROUND_MUSIC)),
                "move": pygame.mixer.Sound(str(constant.MOVE_SOUND)),
                "win": pygame.mixer.Sound(str(constant.WIN_SOUND)),
            }
            self.sounds["background"].set_volume(constant.BACKGROUND_VOLUME)
            self.sounds["move"].set_volume(constant.EFFECT_VOLUME)
            self.sounds["win"].set_volume(constant.EFFECT_VOLUME)
            self.sounds["background"].play(loops=-1)
        except (FileNotFoundError, pygame.error):
            self.sounds = {}

    def start_game(self, where_are_you: int = 0) -> None:
        if where_are_you != 0:
            raise ValueError("only local two-player mode is supported")
        self.run()

    def run(self, max_frames: int | None = None) -> None:
        self.initialize()
        self.running = True
        frame_count = 0
        try:
            while self.running:
                for event in pygame.event.get():
                    self.handle_event(event)
                self.render()
                pygame.display.flip()
                assert self.clock is not None
                self.clock.tick(constant.FPS)
                frame_count += 1
                if max_frames is not None and frame_count >= max_frames:
                    self.running = False
        finally:
            self.shutdown()

    def shutdown(self) -> None:
        for sound in self.sounds.values():
            sound.stop()
        self.sounds = {}
        pygame.quit()
        self.initialized = False

    def handle_event(self, event: pygame.event.Event) -> None:
        if event.type == pygame.QUIT:
            self.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.running = False
            elif event.key == pygame.K_r:
                self.restart()
            elif event.key == pygame.K_m:
                self.toggle_mute()
        elif event.type == pygame.MOUSEMOTION:
            self.hovered = self.position_to_cell(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._handle_click(event.pos)

    def _handle_click(self, position: tuple[int, int]) -> None:
        if self.restart_button.collidepoint(position):
            self.restart()
            return
        if self.sound_button.collidepoint(position):
            self.toggle_mute()
            return

        cell = self.position_to_cell(position)
        if cell is None:
            self.selected = None
            return
        if self.game.is_over:
            return

        row, column = cell
        clicked_piece = self.game.board[row][column]
        if self.selected is None:
            if clicked_piece == self.game.current_player:
                self.selected = cell
            return

        if cell == self.selected:
            self.selected = None
            return
        if clicked_piece == self.game.current_player:
            self.selected = cell
            return

        legal_move = next(
            (move for move in self.game.moves_from(self.selected) if move.end == cell),
            None,
        )
        if legal_move is None:
            return

        self.game.play(self.selected, cell)
        self.selected = None
        self._play_sound("move")
        if self.game.is_over:
            self._stop_sound("background")
            self._play_sound("win")

    def restart(self) -> None:
        self.game = GameState()
        self.selected = None
        self.hovered = None
        self._stop_sound("win")
        self._stop_sound("background")
        if not self.muted and "background" in self.sounds:
            self.sounds["background"].play(loops=-1)

    def toggle_mute(self) -> None:
        self.muted = not self.muted
        if self.muted:
            for sound in self.sounds.values():
                sound.stop()
        elif "background" in self.sounds and not self.game.is_over:
            self.sounds["background"].play(loops=-1)

    def _play_sound(self, name: str) -> None:
        if not self.muted and name in self.sounds:
            self.sounds[name].play()

    def _stop_sound(self, name: str) -> None:
        if name in self.sounds:
            self.sounds[name].stop()

    @staticmethod
    def cell_center(position: Position) -> tuple[int, int]:
        row, column = position
        return (
            constant.BOARD_ORIGIN[0] + column * constant.BOARD_SPACING,
            constant.BOARD_ORIGIN[1] + row * constant.BOARD_SPACING,
        )

    @staticmethod
    def position_to_cell(position: tuple[int, int]) -> Position | None:
        x, y = position
        origin_x, origin_y = constant.BOARD_ORIGIN
        half_spacing = constant.BOARD_SPACING / 2
        if not (
            origin_x - half_spacing
            <= x
            <= origin_x + 4 * constant.BOARD_SPACING + half_spacing
            and origin_y - half_spacing
            <= y
            <= origin_y + 4 * constant.BOARD_SPACING + half_spacing
        ):
            return None

        column = round((x - origin_x) / constant.BOARD_SPACING)
        row = round((y - origin_y) / constant.BOARD_SPACING)
        if 0 <= row < BOARD_SIZE and 0 <= column < BOARD_SIZE:
            return row, column
        return None

    def render(self) -> None:
        assert self.window is not None
        assert self.background is not None
        self.window.blit(self.background, (0, 0))
        wash = pygame.Surface(constant.WINDOW_SIZE, pygame.SRCALPHA)
        wash.fill((255, 255, 255, 42))
        self.window.blit(wash, (0, 0))

        self._draw_top_bar()
        self._draw_board()
        self._draw_move_hints()
        self._draw_pieces()
        if self.game.is_over:
            self._draw_winner_band()

    def _draw_top_bar(self) -> None:
        assert self.window is not None
        panel = pygame.Surface((constant.WINDOW_SIZE[0], 72), pygame.SRCALPHA)
        panel.fill(constant.COLORS["panel"])
        self.window.blit(panel, (0, 0))
        self._draw_button(self.restart_button, "重新开始")
        self._draw_button(self.sound_button, "静音" if not self.muted else "声音")

        child_count = count_pieces(self.game.board, Piece.CHILD)
        tiger_count = count_pieces(self.game.board, Piece.TIGER)
        player_name = "老虎" if self.game.current_player is Player.TIGER else "小孩"
        status = f"{player_name}回合   小孩 {child_count}   老虎 {tiger_count}"
        self._draw_text(status, (400, 38), constant.COLORS["ink"], self.font)

    def _draw_button(self, rectangle: pygame.Rect, label: str) -> None:
        assert self.window is not None
        pygame.draw.rect(
            self.window,
            constant.COLORS["button"],
            rectangle,
            border_radius=5,
        )
        pygame.draw.rect(
            self.window,
            constant.COLORS["button_border"],
            rectangle,
            width=2,
            border_radius=5,
        )
        self._draw_text(
            label, rectangle.center, constant.COLORS["ink"], self.small_font
        )

    def _draw_board(self) -> None:
        assert self.window is not None
        origin_x, origin_y = constant.BOARD_ORIGIN
        extent = constant.BOARD_SPACING * (BOARD_SIZE - 1)
        for index in range(BOARD_SIZE):
            offset = index * constant.BOARD_SPACING
            pygame.draw.line(
                self.window,
                constant.COLORS["board"],
                (origin_x, origin_y + offset),
                (origin_x + extent, origin_y + offset),
                constant.BOARD_LINE_WIDTH,
            )
            pygame.draw.line(
                self.window,
                constant.COLORS["board"],
                (origin_x + offset, origin_y),
                (origin_x + offset, origin_y + extent),
                constant.BOARD_LINE_WIDTH,
            )
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                pygame.draw.circle(
                    self.window,
                    constant.COLORS["board"],
                    self.cell_center((row, column)),
                    6,
                )

    def _draw_move_hints(self) -> None:
        assert self.window is not None
        if self.selected is None:
            return
        for move in self.game.moves_from(self.selected):
            color = (
                constant.COLORS["capture"]
                if move.is_capture
                else constant.COLORS["legal"]
            )
            center = self.cell_center(move.end)
            pygame.draw.circle(self.window, color, center, 22, width=5)

    def _draw_pieces(self) -> None:
        assert self.window is not None
        for row in range(BOARD_SIZE):
            for column in range(BOARD_SIZE):
                piece = Piece(self.game.board[row][column])
                if piece is Piece.EMPTY:
                    continue
                center = self.cell_center((row, column))
                if piece is Piece.CHILD:
                    image = self.child_images[
                        (row * BOARD_SIZE + column) % len(self.child_images)
                    ]
                else:
                    image = self.tiger_images[(row + column) % len(self.tiger_images)]
                rectangle = image.get_rect(center=center)
                self.window.blit(image, rectangle)

                if (row, column) == self.selected:
                    color = (
                        constant.COLORS["tiger"]
                        if piece is Piece.TIGER
                        else constant.COLORS["child"]
                    )
                    pygame.draw.circle(self.window, color, center, 52, width=5)
                elif (
                    (row, column) == self.hovered
                    and piece == self.game.current_player
                    and not self.game.is_over
                ):
                    pygame.draw.circle(
                        self.window,
                        constant.COLORS["button_border"],
                        center,
                        49,
                        width=2,
                    )

    def _draw_winner_band(self) -> None:
        assert self.window is not None
        band = pygame.Surface((constant.WINDOW_SIZE[0], 132), pygame.SRCALPHA)
        band.fill(constant.COLORS["overlay"])
        self.window.blit(band, (0, 255))
        if self.game.is_draw:
            label = "平局"
        else:
            label = (
                "老虎胜利" if self.game.winning_player is Player.TIGER else "小孩胜利"
            )
        self._draw_text(label, (400, 321), constant.COLORS["white"], self.winner_font)

    def _draw_text(
        self,
        text: str,
        center: tuple[int, int],
        color: tuple[int, ...],
        font: pygame.font.Font | None,
    ) -> None:
        assert self.window is not None
        assert font is not None
        surface = font.render(text, True, color)
        self.window.blit(surface, surface.get_rect(center=center))
