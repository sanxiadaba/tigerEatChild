from mcts import mcts
from constant import boardStart
from someFunction import getAllPossible,isOver,whoIsWin
from copy import deepcopy

# 打印输出结果的解释
explainStr = """
前两个参数表示要移动棋子的行列坐标(均从0开始计数)，第三个参数表示棋手的身份（-1表示人 1表示老虎） 第四个参数表示是否执行‘吃’的动作 最后一个参数表示向哪个方向移动（1表示上 2表示下 3表示左 4表示右"""

class board():
    def __init__(self):
        # 人对应矩阵的位置为-1 老虎为1
        self.board = boardStart
        self.currentPlayer = 1
    # 获取当前的选手
    def getCurrentPlayer(self):
        return self.currentPlayer

    # 获取当前的所有可能
    def getPossibleActions(self):
        lin = getAllPossible(self.board, self.currentPlayer)
        return [Action(i) for i in lin]

    # 设置采取某种可能后变化的新情况
    def takeAction(self, action):
        newBoard = deepcopy(self)
        newBoard.board[action.x][action.y] = 0
        if action.role==-1:
            if action.direction==1:
                newBoard.board[action.x-1][action.y]=-1
            elif action.direction==2:
                newBoard.board[action.x + 1][action.y] = -1
            elif action.direction==3:
                newBoard.board[action.x ][action.y-1] = -1
            elif action.direction==4:
                newBoard.board[action.x ][action.y+1] = -1
        else:
            # 在不吃的情况下变换坐标
            if action.isEat==0:
                if action.direction == 1:
                    newBoard.board[action.x - 1][action.y] = 1
                elif action.direction == 2:
                    newBoard.board[action.x + 1][action.y] = 1
                elif action.direction == 3:
                    newBoard.board[action.x][action.y - 1] = 1
                elif action.direction == 4:
                    newBoard.board[action.x][action.y + 1] = 1
            # 在吃的情况下进行坐标变换
            else:
                if action.direction == 1:
                    newBoard.board[action.x - 2][action.y] = 1
                elif action.direction == 2:
                    newBoard.board[action.x + 2][action.y] = 1
                elif action.direction == 3:
                    newBoard.board[action.x][action.y - 2] = 1
                elif action.direction == 4:
                    newBoard.board[action.x][action.y + 2] = 1
        # 变换完之后选手自然也跟着变化
        newBoard.currentPlayer=self.currentPlayer*(-1)
        return newBoard

        # 判断是否结束
    def isTerminal(self):
        return isOver(self.board)

    # 返回分数了
    def getReward(self):
       if  self.isTerminal():
           return 1
       else:
           return False
    def reWinner(self):
        return whoIsWin(self.board)

class Action():
    def __init__(self, tup):
        self.tup = tup
        self.x = self.tup[0]
        self.y = self.tup[1]
        self.role = self.tup[2]
        self.isEat = self.tup[3]
        self.direction = self.tup[4]

    # 这里是重写那几个方法，不用多管
    def __str__(self):
        return (str(self.tup)+explainStr)

    def __repr__(self):
        return (str(self.tup)+explainStr)

    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.tup == other.tup

    def __hash__(self):
        return hash((self.tup))


if __name__=="__main__":
    board = board()
    board.board=[[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1,1, 1, 1, 1], [-1, -1, 0, 0, 0], [1, 0, 0, 0, 0]]
    board.currentPlayer=-1
    # 初始化搜索树  里面的第一个参数是搜索几次 第二个是搜索多少毫秒（二者之间一定要有一个为none）
    searcher = mcts(iterationLimit=None,timeLimit=2000)
    # 这里的initialState就是上面定义的类 而needDetails=True 意思是显示此时胜率
    # 此时的action是一个字典  你可以return action["action"] 或者 return action["expectedReward"] 查看胜率
    action = searcher.search(initialState=board,needDetails=True)
    # 这里输出的action右文字，是因为在上面重写的__str__方法
    print(action)
    print(action["action"])
    print(action["expectedReward"])


    # import random
    # state=board()
    # state.currentPlayer=1
    # state.board=[[1, 1, 1, 1, 1], [1, 1, 1, 1, 1], [1,1, 1, 1, 1], [0, 0, 0, 0, 0], [0, 0, 0, 0, 0]]
    # print(state.board)
    # action = random.choice(state.getPossibleActions())
    # print(action)
    # print(state.isTerminal())

