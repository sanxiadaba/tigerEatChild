import pygame
import constant
from random import choice
from collections import deque
from someFunction import whatMyRole,whoIsWin


class displayGame():
    def __init__(self):
        # 一个用来判断游戏是否结束的参数
        self.isOver=False
        self.board = constant.boardStart
        # 表示棋盘状态的矩阵  人为 1 能活动的老虎为2  没子为0 被困住的老虎为-1
        self.ininGame()
        self.imgGame()
        self.textGame()
        self.suCai()
        self.ininMusic()
        self.imageDict = self.imgOfDict()

    # 开始游戏
    def startGame(self, whereAreYou):
        self.draw()
        self.whereAreYou = whereAreYou
        # 第一次刷新界面
        pygame.display.flip()
        # 这里设置两个处理过的surface(为以后设置透明度的素材）
        self.judge()

    # 初始化游戏的一些最基本设置
    def ininGame(self):
        # 初始化游戏
        pygame.init()
        # 设置游戏标题
        pygame.display.set_caption(constant.playTitle)
        # 设置窗口大小
        self.window = pygame.display.set_mode((constant.window_width, constant.window_height))
        # 设置最开始的填充背景
        self.window.fill(constant.fillColor)
        # 设置fpx
        self.fclock = pygame.time.Clock()
        # 这里是设置红框与蓝框的透明度
        self.tou_b = 255
        self.tou_r = 255
        # 查看相对于当前设备相对于（1280*720）的放大率
        self.rate = constant.rate
        # 棋盘画线左上角的x,y坐标（这里是为了适应不同分辨率下的环境进行的操作）
        self.x_start = (3 / 16) * 800 * self.rate[0]
        self.y_start = (15 / 130) * 650 * self.rate[1]
        # 这里做一些设置，红蓝光标每次只显示一个 这个指定大小的容器用来不断判定posToArea 并将前一个透明度设置为0(其实后来证明要想只显示一个框根本不需要这样(doge))
        self.only = deque(maxlen=2)
        self.lin = (-1, -1)
        self.suo = [False, (-1, -1)]
        # 这里先初始化一个值，方便后续判定
        self.only.append((-1, -1))

    def ininMusic(self):
        musicBgmFile="./static/bgm/"+constant.musicBgm
        musicMoveFile="./static/bgm/"+constant.musicMove
        musicWinFile="./static/bgm/"+constant.musicWin
        # 初始化游戏音乐
        pygame.mixer.init()
        # 加载音乐  这里是bgm音乐
        self.musicBgm=pygame.mixer.Sound(musicBgmFile)
        self.musicBgm.set_volume(constant.musicLoud)
        # 加载移动的音乐
        self.MusicMove=pygame.mixer.Sound(musicMoveFile)
        # 加载胜利的音乐
        self.MusicWin = pygame.mixer.Sound(musicWinFile)
        self.MusicWin.set_volume(constant.musicLoud)
        # 开始播放背景音乐
        self.musicBgm.play(-1,0)

    # 这里事先加载、处理要用的图片
    def imgGame(self):
        # 设置图标
        icon = pygame.image.load("./static/img/" + constant.icon)
        pygame.display.set_icon(icon)
        # 设置人与老虎的大小  # 注意，这里改了之后老虎与小人不一定在其正中心
        imagePeopleSize = (100 * self.rate[0], 100 * self.rate[1])
        # 加载相关需要渲染的图片
        # 背景图片
        self.imagePlay = pygame.image.load("./static/img/" + constant.imameOfPlaySource)

        # 蓝色闪烁的图片
        self.blue_bg = pygame.transform.scale(pygame.image.load("./static/img/" + constant.blue_bg),
                                              (78 * self.rate[0], 78 * self.rate[1])).convert_alpha()

        # 红色闪烁的边框图片
        self.red_bg = pygame.transform.scale(pygame.image.load("./static/img/" + constant.red_bg),
                                             (120 * self.rate[0], 120 * self.rate[1])).convert_alpha()
        # 老虎1
        self.tiger1 = pygame.transform.scale(pygame.image.load("./static/img/" + "tiger1.png"), imagePeopleSize)
        # 老虎2
        self.tiger2 = pygame.transform.scale(pygame.image.load("./static/img/" + "tiger2.png"), imagePeopleSize)
        # 人1
        self.people1 = pygame.transform.scale(pygame.image.load("./static/img/" + "people1.png"), imagePeopleSize)
        # 人2
        self.people2 = pygame.transform.scale(pygame.image.load("./static/img/" + "people2.png"), imagePeopleSize)
        # 人3
        self.people3 = pygame.transform.scale(pygame.image.load("./static/img/" + "people3.png"), imagePeopleSize)

    # 字体、文字的一些基本设置
    def textGame(self):
        # 设置字体
        self.font = pygame.font.Font("./static/font/" + constant.fontSelect, constant.fontSize)
        self.text_1 = self.font.render('人物已锁定', True, constant.getColorRgb("Black"))
        self.text_2 = self.font.render('人物已解除锁定', True, constant.getColorRgb("Black"))
        self.text_3 = self.font.render('老虎胜利', True, constant.getColorRgb("Black"))
        self.text_4 = self.font.render('小孩胜利', True, constant.getColorRgb("Black"))


    # 返回一个每个坐标对应的字典
    def imgOfDict(self):
        # 为了达到随机取的效果 先暂时放在一个列表里，到时候随机取，并记录下来
        self.imageCollectionPeople = [self.people1, self.people2, self.people3]
        self.imageCollectionTiger = [self.tiger1, self.tiger2]

        # 用字典存储每个值对应的图片 这里虽说分别是1，2，3，4，5 但很简单姐可以甄别到底是老虎还是人 而且达到随机取的作用
        imageDict = {}
        # 这里的 1，2，3足以判定谁是人 谁是老虎
        for i in range(5):
            for j in range(5):
                lin = self.board[i][j]
                if lin == 0:
                    imageDict[(i, j)] = 0
                elif lin == -1:
                    imageDict[(i, j)] = choice([1, 2, 3])
                else:
                    imageDict[(i, j)] = choice([4, 5])
        return imageDict

    # 对区域进行划分 #即传入一个坐标，再判定该它属于self.board.board的哪一个(i,j)
    def posToArea(self, pos):
        # 点击按钮在区域范围内才生效
        if pos[0] < (self.x_start - constant.jiange_h / 2) or pos[0] > (self.x_start + constant.jiange_h * 9 / 2) or \
                pos[1] < (self.y_start - constant.jiange_s / 2) or pos[1] > (self.x_start + constant.jiange_s * 9 / 2):
            return False
        else:
            pos = (pos[0] - (self.x_start - constant.jiange_h / 2), pos[1] - (self.y_start - constant.jiange_s / 2))
            x_lin = pos[0] // constant.jiange_h
            y_lin = pos[1] // constant.jiange_s
            return (y_lin, x_lin)

    # 这里渲染的是横竖线
    def drawBackGround(self):
        # 渲染最开始背景
        self.window.blit(self.imagePlay, (0, 0))
        # 画横线
        for i in range(5):
            pygame.draw.line(self.window, constant.lineDrawingColor,
                             (self.x_start, self.y_start + i * constant.jiange_s),
                             (self.x_start + 4 * constant.jiange_h, self.y_start + i * constant.jiange_s),
                             constant.lineWidth)
        # 画竖线
        for i in range(5):
            pygame.draw.line(self.window, constant.lineDrawingColor,
                             (self.x_start + constant.jiange_h * i, self.y_start),
                             (self.x_start + i * constant.jiange_h, self.y_start + 4 * constant.jiange_s),
                             constant.lineWidth)

    # 开始画老虎和人
    def drawTigerAndPeople(self):
        # 对imageDict进行便利  小于等于3的是人 大于等于三的老虎  并且画出对应的随机图像
        for i, j in self.imageDict.items():
            if j != 0:
                if j >= 4:
                    go = self.imageCollectionTiger[4 - j]
                    self.window.blit(go, (self.x_start - 50 * self.rate[0] + i[1] * self.rate[0] * 125,
                                          self.y_start - 65 * self.rate[0] + i[0] * self.rate[1] * 125))
                else:
                    go = self.imageCollectionPeople[3 - j]
                    self.window.blit(go, (self.x_start - 50 * self.rate[0] + i[1] * self.rate[0] * 125,
                                          self.y_start - 55 * self.rate[0] + i[0] * self.rate[1] * 125))
            else:
                pass

    def suCai(self):
        self.blue_tou = pygame.Surface((self.blue_bg.get_width(), self.blue_bg.get_height())).convert()
        self.red_tou = pygame.Surface((self.red_bg.get_width(), self.red_bg.get_height())).convert()

    # 用这个函数来渲染红蓝框  第一个参数是透明度 第二个参数是要放的位置 第三个参数是经过变化的一个surface 第四选择一个蓝框或红框
    def shineRedBlue(self, tou, pos_lin, surface, color):
        self.drawBackGround()
        self.drawTigerAndPeople()
        surface.blit(self.window, (-pos_lin[0], -pos_lin[1]))
        surface.blit(color, (0, 0))
        surface.set_alpha(tou)
        self.window.blit(surface, pos_lin)

    def draw(self):
        self.drawBackGround()
        self.drawTigerAndPeople()

    # 这里写的太臃肿了，但奈何已成屎山（doge)
    def judge(self):
        while True:
            # 当有事件响应时才运行
            for event in pygame.event.get():
                # 判断退出按钮
                if event.type == pygame.QUIT:
                    exit()
                    # 判断是否有鼠标按下
                    # 判断如果按esc键也退出
                elif event.type == pygame.KEYDOWN:
                    if (event.key) == 27:
                        exit()
                # 这里设置锁与不锁
                # 在不锁的情况下
                # 在未分出胜负的情况下
                elif event.type == pygame.MOUSEBUTTONDOWN and self.isOver is False :
                    # 如果没有锁
                    if self.suo[0] == False:
                        # 如果点击不在区域
                        self.lin = self.posToArea(event.pos)
                        if self.lin == False:
                            pass
                        else:
                            if self.whereAreYou == 0:
                                if self.imageDict[self.lin] == 0:
                                    pass
                                else:
                                    # 变成锁住的情况
                                    self.suo[0] = True
                                    self.suo[-1] = self.lin
                                    # 显示已经上锁
                                    self.window.blit(self.text_1, (0, 0))
                                    pygame.display.update()

                    # 在上锁的情况下
                    else:
                        # 在锁的情况下进行鼠标操作 可以解除锁定 选择移动图像
                        self.lin = self.posToArea(event.pos)
                        if self.lin == False:
                            pass
                        else:
                            # 如果点击的区域不是原来的区域
                            if self.lin != self.suo[-1]:
                                # 判断这是什么模式
                                if self.whereAreYou == 0:
                                    # 该人走的情况下
                                    if 0 < self.imageDict[self.suo[-1]] <= 3:
                                        if self.imageDict[self.lin] == 0:
                                            # 如果移动是合法的（最多只能向附近移动一格）
                                            if (abs(self.lin[0] - self.suo[-1][0]) == 1 and abs(
                                                    self.lin[1] - self.suo[-1][1] == 0)) or (
                                                    abs(self.lin[1] - self.suo[-1][1]) == 1 and abs(
                                                self.lin[0] - self.suo[-1][0]) == 0):
                                                # print(1)
                                                self.imageDict[self.lin] = self.imageDict[self.suo[-1]]

                                                self.imageDict[self.suo[-1]] = 0
                                                # 把移动后的点更新为-1
                                                self.board[int(self.lin[0])][int(self.lin[1])] = -1
                                                # 把移动之前的点更新为0
                                                self.board[int(self.suo[-1][0])][int(self.suo[-1][1])]=0
                                                self.suo[0] = False
                                                # self.suo[-1]=(-1,-1)
                                                self.draw()
                                                pygame.display.update()
                                                self.MusicMove.play()
                                    elif self.imageDict[self.suo[-1]] > 3:
                                        # 这是老虎走一步不吃人的情况
                                        if (abs(self.lin[0] - self.suo[-1][0]) == 1 and abs(
                                                self.lin[1] - self.suo[-1][1] == 0)) or (
                                                abs(self.lin[1] - self.suo[-1][1]) == 1 and abs(
                                            self.lin[0] - self.suo[-1][0]) == 0):
                                            self.imageDict[self.lin] = self.imageDict[self.suo[-1]]
                                            self.imageDict[self.suo[-1]] = 0
                                            # 把移动后的点更新为1
                                            self.board[int(self.lin[0])][int(self.lin[1])] = 1
                                            # 把移动之前的点更新为0
                                            self.board[int(self.suo[-1][0])][int(self.suo[-1][1])] = 0
                                            self.suo[0] = False
                                            self.draw()
                                            pygame.display.update()
                                            self.MusicMove.play()
                                        # 老虎走两步吃人的情况下
                                        x_lin = max(self.lin[0], self.suo[-1][0])
                                        y_ln = max(self.lin[1], self.suo[-1][1])
                                        # print(x_lin,y_ln)
                                        if ((abs(self.lin[0] - self.suo[-1][0]) == 2 and abs(
                                                self.lin[1] - self.suo[-1][1] == 0) and (
                                                    self.imageDict[(x_lin - 1, y_ln)] == 0) and (whatMyRole(self.imageDict[(self.lin[0],self.lin[1])])==-1)) or (
                                                abs(self.lin[1] - self.suo[-1][1]) == 2 and abs(
                                            self.lin[0] - self.suo[-1][0]) == 0 and (
                                                        self.imageDict[(x_lin, y_ln - 1)] == 0) and (whatMyRole(self.imageDict[(self.lin[0],self.lin[1])])==-1))):
                                            self.imageDict[self.lin] = self.imageDict[self.suo[-1]]
                                            self.imageDict[self.suo[-1]] = 0
                                            # 把移动后的点更新为1
                                            # print(self.board)
                                            # print(self.lin)
                                            self.board[int(self.lin[0])][int(self.lin[1])] = 1
                                            # 把移动之前的点更新为0
                                            self.board[int(self.suo[-1][0])][int(self.suo[-1][1])] = 0
                                            self.suo[0] = False
                                            # self.suo[-1]=(-1,-1)
                                            self.draw()
                                            pygame.display.update()
                                            self.MusicMove.play()

                            # 如果点击的是原来的位置
                            else:
                                self.suo[0] = False
                                self.window.blit(self.text_2, (0, 0))
                                self.suo[0] = False
                                self.draw()
                                pygame.display.update()

                        # pygame.display.update()

            if self.suo[0] == False :
                try:
                    self.lin = self.posToArea(event.pos)
                    # 这里设置善什么颜色的框
                    if self.lin == False:
                        pass
                    else:
                        # 这里引入only减少渲染压力
                        if self.lin == self.only[-1]:
                            pass
                        else:
                            self.only.append(self.lin)
                            # 如果没有锁
                            # 如果它是人的响应
                            if self.imageDict[self.lin] == 0:
                                pass
                            else:
                                if 0 < self.imageDict[self.lin] <= 3:
                                    self.pos_lin = (
                                        self.x_start + self.only[-1][1] * constant.jiange_h - 41 * self.rate[0],
                                        self.y_start + self.only[-1][0] * constant.jiange_s - 37 * self.rate[1])
                                    if self.whereAreYou == -1 or self.whereAreYou == 0:

                                        self.shineRedBlue(self.tou_b, self.pos_lin, self.blue_tou, self.blue_bg)
                                    else:
                                        pass
                                elif self.imageDict[self.lin] >= 4:
                                    # 红色按钮开始闪烁
                                    self.pos_lin = (
                                        self.x_start + self.only[-1][1] * constant.jiange_h - 59 * self.rate[0],
                                        self.y_start + self.only[-1][0] * constant.jiange_s - 72 * self.rate[1])
                                    if self.whereAreYou == 1 or self.whereAreYou == 0:
                                        self.shineRedBlue(self.tou_r, self.pos_lin, self.red_tou, self.red_bg)
                                pygame.display.update()
                except:
                    pass

            judgeWin=whoIsWin(self.board)
            if judgeWin==0:
                pass
            else:
                self.musicBgm.stop()
                self.MusicWin.play()
                self.suo[0]=True
                # 老虎胜利
                if judgeWin==1:
                    self.draw()
                    self.window.blit(self.text_3, (0, 0))
                # 人胜利
                else:
                    self.draw()
                    self.window.blit(self.text_4, (0, 0))
                pygame.display.update()

            self.fclock.tick(constant.FPX)


