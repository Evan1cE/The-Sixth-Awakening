"""全局常量：动作、阶段、地图字符、屏幕尺寸。

把"魔法值"集中在这里，改规则或改界面时只需要动这一个文件。
例如想把动作上限从 5 改成 6，只改 MAX_RECORDED_ACTIONS 即可
（注意：关卡设计是按 5 步验证过的，改之前先看 README 的关卡说明）。
"""

from enum import Enum

# --------------------------------------------------------------------------
# 屏幕尺寸（课程硬性要求：所有绘制与输入都必须落在 80 列 x 24 行之内）
# --------------------------------------------------------------------------
SCREEN_WIDTH = 80
SCREEN_HEIGHT = 24

# 记忆晶片最多保存几个动作
MAX_RECORDED_ACTIONS = 5


# --------------------------------------------------------------------------
# 动作：第一版只有四个方向和等待，不记录推箱与交互
# 用 Enum 而不是字符串，避免逻辑里到处散落拼写错误。
# --------------------------------------------------------------------------
class Action(Enum):
    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    WAIT = "wait"


# 每个动作对应的格子位移；WAIT 不移动
ACTION_OFFSET = {
    Action.UP: (0, -1),
    Action.DOWN: (0, 1),
    Action.LEFT: (-1, 0),
    Action.RIGHT: (1, 0),
    Action.WAIT: (0, 0),
}

# 界面上的长名字
ACTION_LABEL = {
    Action.UP: "UP",
    Action.DOWN: "DOWN",
    Action.LEFT: "LEFT",
    Action.RIGHT: "RIGHT",
    Action.WAIT: "WAIT",
}

# 界面上的单字符记号（记录槽用）
ACTION_SHORT = {
    Action.UP: "^",
    Action.DOWN: "v",
    Action.LEFT: "<",
    Action.RIGHT: ">",
    Action.WAIT: "~",
}

# 指令 -> 动作。同时接受 WASD 和英文单词，方便不同习惯的玩家。
MOVE_KEYS = {
    "w": Action.UP,
    "a": Action.LEFT,
    "s": Action.DOWN,
    "d": Action.RIGHT,
    "x": Action.WAIT,
    "up": Action.UP,
    "left": Action.LEFT,
    "down": Action.DOWN,
    "right": Action.RIGHT,
    "wait": Action.WAIT,
}


# --------------------------------------------------------------------------
# 游戏阶段
# --------------------------------------------------------------------------
class Phase(Enum):
    EXPLORE = "exploration"   # 探索：移动、推箱、拾取
    RECORD = "recording"      # 录制：只收集指令，不推进房间
    EXECUTE = "execution"     # 执行：回声与玩家每回合同时行动
    WIN = "victory"


# --------------------------------------------------------------------------
# 地图字符
# 静态地图只存墙与地板；R / A / D / B / E / G 是固定装置，
# 木箱 C 与玩家 P 是动态对象，只出现在关卡字符串里当作初始位置标记。
# --------------------------------------------------------------------------
WALL = "#"
FLOOR = "."
TILE_RECORDER = "R"      # 记忆晶片（拾取后变成地板）
TILE_PLATE_A = "A"       # 配重板：压住后给记录器台供电
TILE_CONSOLE = "D"       # 记录器台 / 重置装置（实体，不能走进去）
TILE_PLATE_B = "B"       # 出口左压力板
TILE_PLATE_E = "E"       # 出口右压力板
TILE_EXIT = "G"          # 出口
TILE_BOX_START = "C"     # 木箱初始位置（动态）
TILE_PLAYER_START = "P"  # 玩家初始位置（动态）

# 这些字符在静态地图里会被替换成地板，真实位置由 GameState 管理
DYNAMIC_MARKERS = (TILE_BOX_START, TILE_PLAYER_START)
