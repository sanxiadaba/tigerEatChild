"""把界面用字抽出来，生成一个几十 KB 的字体子集。

    python tools/make_font.py [源字体]

源字体默认用 Windows 的隶书（simli.ttf）。改过 app.py / config.py / README.md
里的中文后重新跑一次，再提交 static/font/ui.ttf。
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_SOURCE = Path("C:/Windows/Fonts/simli.ttf")
OUTPUT = ROOT / "static" / "font" / "ui.ttf"


def string_literals(path: Path) -> str:
    tree = ast.parse(path.read_text("utf-8"))
    return "".join(
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    )


def main() -> None:
    source = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_SOURCE
    if not source.exists():
        raise SystemExit(f"找不到源字体: {source}")

    text = "".join(string_literals(ROOT / name) for name in ("app.py", "config.py"))
    characters = {chr(code) for code in range(32, 127)}
    characters.update(char for char in text if ord(char) > 127)

    options = subset.Options()
    options.layout_features = []
    options.name_IDs = ["*"]
    options.name_legacy = True
    options.notdef_outline = True
    options.recalc_bounds = True
    options.recalc_timestamp = False
    options.drop_tables += ["DSIG"]

    font = TTFont(str(source))
    subsetter = subset.Subsetter(options=options)
    subsetter.populate(text="".join(sorted(characters)))
    subsetter.subset(font)
    font.save(OUTPUT)
    print(f"{OUTPUT.relative_to(ROOT)}: {len(characters)} chars, {OUTPUT.stat().st_size} bytes")


if __name__ == "__main__":
    main()
