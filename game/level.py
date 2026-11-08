"""关卡定义：唯一一张 9 x 7 的档案室地图。

设计文档里的初始布置（x 向右、y 向下，左上角为 (0, 0)）：

    y=0  #########
    y=1  #..R....#
    y=2  #..C..A.#
    y=3  #P..D...#
    y=4  #..B..E.#
    y=5  #...G...#
    y=6  #########

对象坐标与符号含义见设计文档第三节的表。
所有坐标都写成常量，重置、渲染、测试都从这里取，避免各自硬编码。
"""

from dataclasses import dataclass
from typing import Tuple

from .constants import DYNAMIC_MARKERS, FLOOR
from .position import Pos

# --------------------------------------------------------------------------
# 房间原始布局（"C" 和 "P" 只是初始位置标记，静态地图里会被当成地板）
# --------------------------------------------------------------------------
LEVEL_ROWS = (
    "#########",
    "#..R....#",
    "#..C..A.#",
    "#P..D...#",
    "#..B..E.#",
    "#...G...#",
    "#########",
)

# --------------------------------------------------------------------------
# 关键坐标
# --------------------------------------------------------------------------
PLAYER_START = Pos(1, 3)       # P：玩家起点 / 每轮回到的入口
ECHO_START = Pos(1, 3)         # 回声投影起点：和入口同一格
BOX_START = Pos(3, 2)          # C：木箱初始位置
RECORDER_ITEM = Pos(3, 1)      # R：记忆晶片
CONSOLE = Pos(4, 3)            # D：记录器台 / 重置装置
WEIGHT_PLATE = Pos(6, 2)       # A：配重板，压住后记录器台通电
EXIT_PLATE_LEFT = Pos(3, 4)    # B：出口左压力板
EXIT_PLATE_RIGHT = Pos(6, 4)   # E：出口右压力板
EXIT_TILE = Pos(4, 5)          # G：出口


@dataclass(frozen=True)
class Level:
    """一份不可变的关卡描述。

    frozen=True 表示创建后不能改：关卡是只读数据，
    所有会变的（玩家、箱子、门）都放在 GameState 里。
    """

    rows: Tuple[str, ...]
    player_start: Pos
    echo_start: Pos
    box_start: Pos
    recorder_item: Pos
    console: Pos
    weight_plate: Pos
    exit_plates: Tuple[Pos, Pos]
    exit_tile: Pos

    @property
    def width(self) -> int:
        return len(self.rows[0])

    @property
    def height(self) -> int:
        return len(self.rows)

    def static_rows(self) -> Tuple[str, ...]:
        """把动态标记（C / P）换成地板后的静态地图。"""
        table = {marker: FLOOR for marker in DYNAMIC_MARKERS}
        return tuple("".join(table.get(ch, ch) for ch in row) for row in self.rows)


# --------------------------------------------------------------------------
# 默认关卡实例（本游戏只有一个房间）
# --------------------------------------------------------------------------
DEFAULT_LEVEL = Level(
    rows=LEVEL_ROWS,
    player_start=PLAYER_START,
    echo_start=ECHO_START,
    box_start=BOX_START,
    recorder_item=RECORDER_ITEM,
    console=CONSOLE,
    weight_plate=WEIGHT_PLATE,
    exit_plates=(EXIT_PLATE_LEFT, EXIT_PLATE_RIGHT),
    exit_tile=EXIT_TILE,
)
