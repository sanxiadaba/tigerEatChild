from someFunction import getScreenResolution,getColorRgb
"""
这里设置游戏的相关参数  
"""
#老虎和小人的图片
tiger1="tiger1.png"
tiger2="tiger2.png"
people1="people1.png"
people2="people2.png"
people3="people3.png"
red_bg="red_bg.png"
blue_bg="blue_bg.png"
# 设置图标
icon="icon.jpg"
# 画棋盘线的粗细
lineWidth=3
# 游戏窗口大小 如果调节的画建议按比例调节
screenSize=(800,650)
# 根据不同分辨率来显示不同大小（本设备分辨率为1280*720 为防止窗口在高分辨率下窗口会变小，所以做了以下设置以适应不同的分辨率）
# 调用函数，获取分辨率 注意函数返回的是一个数组
# 游戏的显示宽度、高度
screenResolution=getScreenResolution()
#表示长与宽
rate=(screenResolution[0]/1280,screenResolution[1]/720)
window_width=screenSize[0]*rate[0]
window_height=screenSize[1]*rate[1]
# 棋盘的间隔(横向间隔和竖项间隔) 下面时横向间隔和竖项间隔
jiange_h=125*rate[0]
jiange_s=125*rate[1]
# 游戏刷新率(一般60足够）
FPX=30
# 玩游戏时背景图路径 自定义的文件放在 static/img/ 目录下
imameOfPlaySource="image1.jpg"
# 字体大小设置
fontSize=50
# 选择使用哪款字体  自定义下载的字体放在static/font/ 目录下
fontSelect="default.TTF"
# 游戏的名称
playTitle="老虎吃小孩"
# 常用的颜色
# 默认页面填充的颜色 被图片遮盖了，暂时不用管
fillColor=getColorRgb("purpleGrey")
# 画棋盘线的颜色
lineDrawingColor=getColorRgb("Navy")

# 人对应矩阵的位置为-1 老虎为1
boardStart=[[0 for i in range(5)] for j in range(5)]
for i in range(5):
    for j in range(5):
        if i==4 and j in [0,2,4]:
            boardStart[i][j]=1
        if i<3:
            boardStart[i][j]=-1

