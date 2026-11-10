# 老虎吃小孩

一个使用 Pygame 实现的 5x5 本地双人棋类游戏。

## 游戏规则

- 小孩共有 15 个，初始位于棋盘上方三排。
- 老虎共有 3 只，初始位于棋盘最下方的左、中、右三个位置。
- 老虎先手，随后双方轮流行动。
- 双方都可以向上、下、左、右移动到相邻空位。
- 老虎还可以越过一个空位，落到同方向两格外的小孩所在格并吃掉该小孩（落点即被吃的那一格）。
- 老虎无法进行任何合法移动时，小孩获胜。
- 小孩全部被吃掉或无法进行任何合法移动时，老虎获胜。
- 相同局面和行棋方第三次出现，或连续 100 个半步（双方各 50 手）没有吃子时，判为平局。

规则判定与行棋方无关：每次走子后都会同时检查双方是否还有合法走法。因此如果双方恰好都无路可走，判小孩获胜（老虎先被判定为无路）。

## 运行

需要 Python 3.10–3.14。依赖是 `pygame-ce`（`import pygame` 完全兼容的社区分支），官方 `pygame==2.6.1` 没有 Python 3.14 的 wheel。

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python main.py
```

也可以直接使用已有 Python 环境：

```powershell
python -m pip install -r requirements.txt
python main.py
```

## 操作

- 鼠标左键选择棋子和目标位置。
- 再次点击已选棋子可取消选择；点击空白处也会取消选择。
- `R` 重新开始，`M` 开关声音，`Esc` 退出。
- 界面会标出当前棋子的合法落点；红色标记表示吃子。
- 对局结束后会显示胜负横幅，按 `R` 重新开始。

## 测试

```powershell
python -m unittest discover -s tests -v
```

测试使用 SDL 的无窗口和静音驱动，不会弹出游戏窗口。

## 代码检查

```powershell
python -m pip install ruff mypy
python -m ruff check .
python -m mypy
```

配置见 `pyproject.toml`；CI（`.github/workflows/ci.yml`）会在 Python 3.10 / 3.12 / 3.14 上跑 lint、类型检查和单元测试。

## 项目结构

- `game_logic.py`：棋盘状态、合法移动、吃子、回合和胜负规则。
- `display_game.py`：Pygame 输入、声音与画面渲染。
- `constant.py`：资源路径和界面参数。
- `main.py`：程序入口。
- `tests/`：规则和界面冒烟测试。

可执行文件应由发布流程从对应源码构建，不在源码仓库中保存过时的打包产物。
