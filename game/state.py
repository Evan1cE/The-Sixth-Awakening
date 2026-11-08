"""动态游戏状态与重置快照。

设计原则（见设计文档第七、八节）：
    * 房间实体（玩家、箱子、门、回声）会随重置复原；
    * "装置知识"（晶片已取走、配重板通过电）跨重置保留，避免重复做同一段操作；
    * 已录制的动作列表放在 GameState 里，重置时**不**清除。
"""

from dataclasses import dataclass, field
from typing import List, Optional

from .constants import Action, Phase
from .level import Level
from .position import Pos


@dataclass
class GameState:
    """一局游戏的全部动态数据。

    只保存"会变"的东西；地图、坐标常量都在 Level 里。
    """

    player: Pos
    box: Pos

    phase: Phase = Phase.EXPLORE
    turn: int = 0          # 当前执行阶段的回合数
    attempt: int = 1       # 第几次"醒来"（每次投影回声 +1）

    echo: Optional[Pos] = None     # 回声位置，未投影时为 None
    echo_index: int = 0            # 回声执行到动作列表的第几步

    actions: List[Action] = field(default_factory=list)  # 已录制的动作（跨重置保留）

    # ---- 跨重置保留的"装置知识" ----
    recorder_taken: bool = False   # 记忆晶片是否已被取走
    power_ever: bool = False       # 配重板是否曾经被压住（记录器台是否通过电）

    # ---- 房间实体状态 ----
    door_open: bool = False        # 出口门是否已锁死为开启
    win: bool = False

    # ------------------------------------------------------------------
    # 构造
    # ------------------------------------------------------------------
    @classmethod
    def new(cls, level: Level) -> "GameState":
        """生成一局全新的游戏（初始快照）。"""
        return cls(player=level.player_start, box=level.box_start)

    # ------------------------------------------------------------------
    # 派生状态
    # ------------------------------------------------------------------
    def device_ready(self) -> bool:
        """记录器台是否可用：既有电，又要有晶片。"""
        return self.power_ever and self.recorder_taken

    def plate_a_pressed(self, level: Level) -> bool:
        """配重板当前是否被箱子压住（这是每回合**实时**结算的）。"""
        return self.box == level.weight_plate

    def exit_plates_pressed(self, level: Level) -> "tuple":
        """返回 (左板是否被占, 右板是否被占)。"""
        occupied = self.occupied_tiles()
        left, right = level.exit_plates
        return left in occupied, right in occupied

    def occupied_tiles(self) -> set:
        """当前所有能压住压力板的占位格（玩家、回声、箱子）。"""
        tiles = {self.player}
        if self.echo is not None:
            tiles.add(self.echo)
        tiles.add(self.box)
        return tiles


@dataclass(frozen=True)
class Snapshot:
    """重置用的房间快照。

    按设计文档，快照只保存房间实体；动作列表与装置知识不在其中。
    """

    player: Pos
    box: Pos
    door_open: bool
    echo: Optional[Pos]
    echo_index: int

    @classmethod
    def capture(cls, state: GameState) -> "Snapshot":
        return cls(
            player=state.player,
            box=state.box,
            door_open=state.door_open,
            echo=state.echo,
            echo_index=state.echo_index,
        )

    def restore(self, state: GameState) -> None:
        """把房间实体恢复成快照里的样子。"""
        state.player = self.player
        state.box = self.box
        state.door_open = self.door_open
        state.echo = self.echo
        state.echo_index = self.echo_index
