"""静态地图查询。

TileMap 只回答"某一格的地形是什么"，不关心玩家/箱子/门的状态；
动态对象一律由 GameState 决定，因此重置逻辑非常干净。
"""

from typing import List

from .constants import WALL
from .level import Level
from .position import Pos


class TileMap:
    """把关卡字符串变成可以按坐标查询的二维表。"""

    def __init__(self, level: Level) -> None:
        # 逐行转成 list，方便按 (x, y) 索引
        self._grid: List[List[str]] = [list(row) for row in level.static_rows()]
        self.width = level.width
        self.height = level.height

    def in_bounds(self, pos: Pos) -> bool:
        """坐标是否落在房间内。"""
        return 0 <= pos.x < self.width and 0 <= pos.y < self.height

    def tile(self, pos: Pos) -> str:
        """返回该格的地形字符；越界时返回墙，让边界判断统一。"""
        if not self.in_bounds(pos):
            return WALL
        return self._grid[pos.y][pos.x]

    def is_wall(self, pos: Pos) -> bool:
        return self.tile(pos) == WALL

    def rows(self):
        """返回可打印的地图行（调试用）。"""
        return ["".join(row) for row in self._grid]
