"""格坐标与位移计算。

用 NamedTuple 而不是自定义类：它自带相等比较、可哈希、可解包，
既可以直接放进 set，也能整包比较两个坐标是否相同。
"""

from typing import NamedTuple


class Pos(NamedTuple):
    """地图上的一个格子。左上角是 (0, 0)，x 向右增大，y 向下增大。"""

    x: int
    y: int

    def shifted(self, dx: int, dy: int) -> "Pos":
        """返回平移后的新坐标（原坐标不变）。"""
        return Pos(self.x + dx, self.y + dy)

    def neighbour(self, action) -> "Pos":
        """返回朝某个动作方向走一格后的坐标。"""
        # 放在函数内部 import，避免 constants 与 position 互相导入时出问题
        from .constants import ACTION_OFFSET

        dx, dy = ACTION_OFFSET[action]
        return Pos(self.x + dx, self.y + dy)

    def is_adjacent_to(self, other: "Pos") -> bool:
        """判断两格是否上下左右相邻（曼哈顿距离恰好为 1）。"""
        return abs(self.x - other.x) + abs(self.y - other.y) == 1

    def __str__(self) -> str:  # 调试与日志用
        return "({x},{y})".format(x=self.x, y=self.y)
