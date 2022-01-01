import tkinter
"""
这里放一些功能函数
"""


# 获取屏幕分辨率（对应的调节窗口的大小）
def getScreenResolution():
    screen = tkinter.Tk()
    # 获取当前屏幕的宽
    x = screen.winfo_screenwidth()
    # 获取当前屏幕的高
    y = screen.winfo_screenheight()
    # 删除屏幕 防止占用资源
    del screen
    return x,y

# 返回颜色的rgb
# 相关网址 https://www.sioe.cn/yingyong/yanse-rgb-16/
def getColorRgb(name):
    dict={
        # 白色
        "White":(255,255,255),
        # 雪白
        "Snow": (255, 250, 250),
        # 纯红
        "Red":(	255,0,0),
        # 火红、砖红
        "FireBrick":(178,34,34),
        # 纯黑
        "Black":(0,0,0),
        # 浅灰色
        "LightGrey":(211,211,211),
        # 纯绿
        "Green":(0,128,0),
        # 紫灰色
        "purpleGrey":(216,191,216),
        # 靛青
        "Indigo":(75,0,130),
        # 深蓝
        "DarkBlue":(0,0,139),
        # 海军蓝
        "Navy":(0,0,128)
    }
    try:
        return dict[str(name)]
    except:
        raise Exception("字典里没有对应的rgb值，请自行添加")


# 插看当前所有可能点  #ju是一个矩阵  player表示选手 这样才能筛选出该怎么走
def getAllPossible(ju,player):
    # 1:上  2 ：下  ：左   4：右
    all=[]
    for i in range(5):
        for j in range(5):
            lin=ju[i][j]
            if lin==0:
                pass
            # 先添加人的所有可能
            elif lin==-1:
                # 这里添加所有可以向上移动的人棋子
                if i==0:
                    pass
                else:
                    if ju[i-1][j]==0:
                        # 添加一个元组，前两个参数表示坐标第三个参数表明这是人还是老虎，第四个参数表明这是正常走还是“吃人”（走的话为1），第五个参数表示它的方向，
                        all.append((i,j,-1,0,1))
                    else:
                        pass
                # 这里添加所有可以向下移动的人的棋子
                if i==4:
                    pass
                else:
                    if ju[i+1][j]==0:
                        all.append((i,j,-1,0,2))
                    else:
                        pass
                # 这里添加所有可以向左移动的人的棋子
                if j==0:
                    pass
                else:
                    if ju[i][j-1]==0:
                        all.append((i,j,-1,0,3))
                    else:
                        pass
                # 这里添加所有可以向右移动的人的棋子
                if j==4:
                    pass
                else:
                    if ju[i][j+1]==0:
                        all.append((i,j,-1,0,4))
                    else:
                        pass
            # 接下来添加老虎的情况
            else:
                # 先添加老虎走一步的情况
                # 这里添加所有可以向上移动的老虎棋子
                if i == 0:
                    pass
                else:
                    if ju[i - 1][j] == 0:
                        # 添加一个元组，前两个参数表示坐标第三个参数表明这是人还是老虎，第四个参数表明这是正常走还是“吃人”（走的话为1），第五个参数表示它的方向，
                        all.append((i, j, 1, 0, 1))
                    else:
                        pass
                # 这里添加所有可以向下移动的老虎的棋子
                if i == 4:
                    pass
                else:
                    if ju[i + 1][j] == 0:
                        all.append((i, j, 1, 0, 2))
                    else:
                        pass
                # 这里添加所有可以向左移动的老虎的棋子
                if j == 0:
                    pass
                else:
                    if ju[i][j - 1] == 0:
                        all.append((i, j, 1, 0, 3))
                    else:
                        pass
                # 这里添加所有可以向右移动的老虎的棋子
                if j == 4:
                    pass
                else:
                    if ju[i][j + 1] == 0:
                        all.append((i, j, 1, 0, 4))
                    else:
                        pass


                # 先添加老虎走两步的情况
                # 这里添加所有可以向上吃子的老虎棋子
                if i <= 1:
                    pass
                else:
                    if ju[i - 2][j] == -1 and ju[i-1][j]==0:
                        # 添加一个元组，前两个参数表示坐标第三个参数表明这是人还是老虎，第四个参数表明这是正常走还是“吃人”（走的话为1），第五个参数表示它的方向，
                        all.append((i, j, 1, 1, 1))
                    else:
                        pass
                # 这里添加所有可以向下吃子的老虎的棋子
                if i >= 3:
                    pass
                else:
                    if ju[i + 2][j] == -1 and ju[i+1][j]==0:
                        all.append((i, j, 1, 1, 2))
                    else:
                        pass
                # 这里添加所有可以向左吃子的老虎的棋子
                if j <= 1:
                    pass
                else:
                    if ju[i][j - 2] == -1 and ju[i][j-1]==0:
                        all.append((i, j, 1, 1, 3))
                    else:
                        pass
                # 这里添加所有可以向右吃子的老虎的棋子
                if j >= 3:
                    pass
                else:
                    if ju[i][j + 2] == -1 and ju[i][j+1]==0:
                        all.append((i, j, 1, 1, 4))
                    else:
                        pass
    # 最后一步的筛选了
    newAll=[i for i in all if i[2]==player]
    return newAll

# 根据一个矩阵，判断是否游戏结束
def isOver(ju):
    # 如果哪一方无棋可走就说明哪方输了
    if len(getAllPossible(ju,1))==0 or len(getAllPossible(ju,-1))==0:
        return True
    else:
        return False

def whoIsWin(ju):
    # 如果老虎可走的步数为0的话说明人胜利了 反之亦然
    if len(getAllPossible(ju, 1)) == 0:
        return -1
    if len(getAllPossible(ju, 0)) == 0:
        return 1

# 将1 2 3 4 5转化为对应的0,1

def whatMyRole(n):
    if 0<n<=3:
        return -1
    elif n>3:
        return 1








