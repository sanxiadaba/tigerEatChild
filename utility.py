"""
这里放一些功能函数
"""
import tkinter
from typing import List, Tuple


# 获取屏幕分辨率（对应的调节窗口的大小）
def get_screen_resolution():
    screen = tkinter.Tk()
    # 获取当前屏幕的宽
    x = screen.winfo_screenwidth()
    # 获取当前屏幕的高
    y = screen.winfo_screenheight()
    # 删除屏幕 防止占用资源
    del screen
    return x, y


# 返回颜色的rgb
# 相关网址 https://www.sioe.cn/yingyong/yanse-rgb-16/
def get_color_rgb(name: str):
    dict = {
        # 白色
        "White": (255, 255, 255),
        # 雪白
        "Snow": (255, 250, 250),
        # 纯红
        "Red": (255, 0, 0),
        # 火红、砖红
        "FireBrick": (178, 34, 34),
        # 纯黑
        "Black": (0, 0, 0),
        # 浅灰色
        "LightGrey": (211, 211, 211),
        # 纯绿
        "Green": (0, 128, 0),
        # 紫灰色
        "purpleGrey": (216, 191, 216),
        # 靛青
        "Indigo": (75, 0, 130),
        # 深蓝
        "DarkBlue": (0, 0, 139),
        # 海军蓝
        "Navy": (0, 0, 128)
    }
    try:
        return dict[str(name)]
    except:
        raise Exception(
            "字典里没有对应的rgb值,可以自行添加:https://www.sioe.cn/yingyong/yanse-rgb-16/")


# 查看当前机器下一步可能走的点
# board是一个矩阵,表示棋盘上所有的点
# 值表示对应的状态
# 人为 0 能活动的老虎为1  没子为-1 被困住的老虎为2
# player表示选手 这样才能筛选出该怎么走(0,1表示人走还是老虎走)
# 返回该选手所有可能的状态元组
def get_all_possible(board: List[int][int], player: int):
    # 储存该player所有可能走的点的元组
    # tuple格式为：(棋盘横坐标、棋盘纵坐标、人还是老虎（人为0，老虎为1）、正常走还是“吃人”（走为0，吃人为1）、方向（上下左右分别对应1，2，3，4）)
    all: List[Tuple[int]] = []
    for i in range(5):
        for j in range(5):
            # 表示当前这个位置坐标的状态
            state = board[i][j]
            # 无子，直接pass
            if state == -1:
                pass
            # 该点为人的所有可能下一步
            elif state == 0 and player == 0:
                # 这里添加所有可以向上移动的人棋子
                # 在最上面一行的棋子，直接pass
                if i == 0:
                    pass
                else:
                    if board[i - 1][j] == -1:
                        all.append((i, j, 0, 0, 1))
                    else:
                        pass
                # 这里添加所有可以向下移动的人的棋子
                # 在最下面，无法再往下，直接pass
                if i == 4:
                    pass
                else:
                    if board[i + 1][j] == -1:
                        all.append((i, j, 0, 0, 2))
                    else:
                        pass
                # 这里添加所有可以向左移动的人的棋子
                # 在最左边一列的棋子，直接pass
                if j == 0:
                    pass
                else:
                    if board[i][j - 1] == -1:
                        all.append((i, j, 0, 0, 3))
                    else:
                        pass
                # 这里添加所有可以向右移动的人的棋子
                # 在最右边一列的棋子，直接pass
                if j == 4:
                    pass
                else:
                    if board[i][j + 1] == -1:
                        all.append((i, j, 0, 0, 4))
                    else:
                        pass
            # 可以动的老虎的情况
            elif state == 1 and player == 1:
                # 先添加老虎走一步的情况
                # 这里添加所有可以向上移动的老虎棋子
                if i == 0:
                    pass
                else:
                    if board[i - 1][j] == -1:
                        all.append((i, j, 1, 0, 1))
                    else:
                        pass
                # 这里添加所有可以向下移动的老虎的棋子
                if i == 4:
                    pass
                else:
                    if board[i + 1][j] == -1:
                        all.append((i, j, 1, 0, 2))
                    else:
                        pass
                # 这里添加所有可以向左移动的老虎的棋子
                if j == 0:
                    pass
                else:
                    if board[i][j - 1] == -1:
                        all.append((i, j, 1, 0, 3))
                    else:
                        pass
                # 这里添加所有可以向右移动的老虎的棋子
                if j == 4:
                    pass
                else:
                    if board[i][j + 1] == -1:
                        all.append((i, j, 1, 0, 4))
                    else:
                        pass

                # 添加老虎走两步的情况(吃小孩)
                # 这里添加所有可以向上吃子的情况
                if i <= 1:
                    pass
                else:
                    # 这里要注意，不仅空余两个格是小孩，还要求中间是空格
                    if board[i - 2][j] == 0 and board[i - 1][j] == -1:
                        all.append((i, j, 1, 1, 1))
                    else:
                        pass
                # 这里添加所有可以向下吃子的老虎的棋子
                if i >= 3:
                    pass
                else:
                    if board[i + 2][j] == 0 and board[i + 1][j] == -1:
                        all.append((i, j, 1, 1, 2))
                    else:
                        pass
                # 这里添加所有可以向左吃子的老虎的棋子
                if j <= 1:
                    pass
                else:
                    if board[i][j - 2] == 0 and board[i][j - 1] == -1:
                        all.append((i, j, 1, 1, 3))
                    else:
                        pass
                # 这里添加所有可以向右吃子的老虎的棋子
                if j >= 3:
                    pass
                else:
                    if board[i][j + 2] == 0 and board[i][j + 1] == -1:
                        all.append((i, j, 1, 1, 4))
                    else:
                        pass
    return all


def who_is_win(board: List[int][int]):
    # 如果老虎可走的步数为0的话说明人胜利了 反之亦然
    if len(get_all_possible(board, 0)) == 0:
        return "tiger"
    if len(get_all_possible(board, 1)) == 0:
        return "people"
    else:
        return "none"


# 根据一个矩阵，判断是否游戏结束
def is_over(board: List[int][int]):
    # 决出胜者就意味着游戏结束
    win = who_is_win(board)
    if win != "none":
        return True
    else:
        return False


# 将1 2 3 4 5转化为对应的0,1


def whatMyRole(n):
    if 0 < n <= 3:
        return -1
    elif n > 3:
        return 1
