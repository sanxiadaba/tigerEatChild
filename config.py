from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_ROOT / "static"
IMAGE_DIR = STATIC_DIR / "img"
AUDIO_DIR = STATIC_DIR / "audio"
FONT_DIR = STATIC_DIR / "font"

WINDOW_SIZE = (1600, 900)
WINDOW_TITLE = "老虎吃小孩"
FPS = 60

TOP_BAR_HEIGHT = 90
BOARD_ORIGIN = (500, 190)
BOARD_SPACING = 150
BOARD_LINE_WIDTH = 5
PIECE_SIZE = (116, 116)
# A click counts when it lands inside this radius around a cell centre, which
# keeps the dead space between pieces from selecting a piece.
HIT_RADIUS = int(BOARD_SPACING * 0.4)
WINNER_BAND_HEIGHT = 240

BACKGROUND_IMAGE = IMAGE_DIR / "background.jpg"
ICON_IMAGE = IMAGE_DIR / "icon.png"
CHILD_IMAGE = IMAGE_DIR / "child.png"
TIGER_IMAGE = IMAGE_DIR / "tiger.png"
FONT_FILE = FONT_DIR / "ui.ttf"

BACKGROUND_MUSIC = AUDIO_DIR / "bgm.mp3"
MOVE_SOUND = AUDIO_DIR / "move.mp3"
WIN_SOUND = AUDIO_DIR / "win.mp3"
BACKGROUND_VOLUME = 0.08
EFFECT_VOLUME = 0.35

COLORS = {
    "ink": (31, 38, 58),
    "board": (38, 54, 92),
    "child": (57, 102, 173),
    "tiger": (184, 62, 57),
    "select": (26, 30, 42),
    "legal": (39, 132, 91),
    "capture": (194, 58, 52),
    "last": (214, 158, 46),
    "panel": (250, 250, 252, 218),
    "button": (255, 255, 255),
    "button_hover": (238, 241, 248),
    "button_disabled": (236, 236, 240),
    "button_border": (77, 84, 107),
    "button_disabled_border": (176, 178, 188),
    "muted_text": (126, 132, 148),
    "overlay": (28, 33, 48, 218),
    "menu_panel": (34, 40, 58, 246),
    "menu_button": (58, 66, 88),
    "menu_button_hover": (76, 86, 112),
    "white": (255, 255, 255),
}
