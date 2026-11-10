from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent
STATIC_DIR = PROJECT_ROOT / "static"
IMAGE_DIR = STATIC_DIR / "img"
AUDIO_DIR = STATIC_DIR / "bgm"
FONT_DIR = STATIC_DIR / "font"

WINDOW_SIZE = (800, 650)
WINDOW_TITLE = "老虎吃小孩"
FPS = 60

BOARD_ORIGIN = (160, 120)
BOARD_SPACING = 120
BOARD_LINE_WIDTH = 4
PIECE_SIZE = (92, 92)
# A click counts when it lands inside this radius around a cell centre, which
# keeps the dead space between pieces from selecting a piece.
BOARD_HIT_RADIUS = int(BOARD_SPACING * 0.4)
WINNER_BAND_HEIGHT = 132

BACKGROUND_IMAGE = IMAGE_DIR / "image1.jpg"
ICON_IMAGE = IMAGE_DIR / "icon.jpg"
CHILD_IMAGES = tuple(IMAGE_DIR / f"people{index}.png" for index in range(1, 5))
TIGER_IMAGES = tuple(IMAGE_DIR / f"tiger{index}.png" for index in range(1, 3))
FONT_FILE = FONT_DIR / "default.TTF"

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
    "legal": (39, 132, 91),
    "capture": (194, 58, 52),
    "panel": (250, 250, 252, 218),
    "button": (255, 255, 255),
    "button_border": (77, 84, 107),
    "overlay": (28, 33, 48, 218),
    "white": (255, 255, 255),
}
