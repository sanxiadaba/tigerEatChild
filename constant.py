from utility import get_color_rgb, get_screen_resolution
"""
这里设置游戏的相关参数  
"""
# 老虎和小人的图片
tiger1 = "tiger1.png"
tiger2 = "tiger2.png"
people1 = "people1.png"
people2 = "people2.png"
people3 = "people3.png"
red_bg = "red_bg.png"
blue_bg = "blue_bg.png"
# 游戏左上角设置图标
icon = "icon.jpg"
# 画棋盘线的粗细
board_line_width = 3
# 游戏窗口大小 如果调节的画建议按比例调节
screen_size = (800, 650)
# 根据不同分辨率来显示不同大小（本设备分辨率为1280*720 为防止窗口在高分辨率下窗口会变小，所以做了以下设置以适应不同的分辨率）
# 调用函数，获取分辨率 注意函数返回的是一个数组
# 游戏的显示宽度、高度
screen_resolution = get_screen_resolution()
# 实际长与宽
rate = (screen_resolution[0] / 1280, screen_resolution[1] / 720)
window_width = screen_size[0] * rate[0]
window_height = screen_size[1] * rate[1]
# 棋盘的间隔(横向间隔和竖项间隔) 下面时横向间隔和竖项间隔
interval_h = 125 * rate[0]
interval_s = 125 * rate[1]
# 游戏刷新率(一般30足够）
fpx = 30
# 玩游戏时背景图路径 自定义的文件放在 static/img/ 目录下
imame_play_source = "image1.jpg"
# 字体大小设置
font_size = 50
# 游戏的名称
play_title = "老虎吃小孩"
# 常用的颜色
# 默认页面填充的颜色 被图片遮盖了，暂时不用管
fill_color = get_color_rgb("purpleGrey")
# 画棋盘线的颜色
line_color = get_color_rgb("Navy")

# 初始化矩阵
# 人对应矩阵的位置为0 老虎为1 无子为-1
board_start = [[-1 for _ in range(5)] for _ in range(5)]
for i in range(5):
    for j in range(5):
        # 老虎
        if i == 4 and j in [1, 3]:
            board_start[i][j] = 1
        # 人
        if i < 3:
            board_start[i][j] = 0
# bgm
music_bgm = "bgm.mp3"
# 移动的音乐
music_move = "move.mp3"
# 分出胜负的音效
music_win = "win.mp3"
# 设置音乐的音量 值越大 声音越大
music_loud = 0.08
