"""记忆晶片：录制、撤销、确认，以及房间重置 / 回声投影。

这一层把"跨重置保留的数据"（动作列表、装置知识）和
"随重置复原的房间实体"（位置、箱子、门）分开处理，
这是设计文档第七节的核心要求。
"""

from collections import deque
from typing import Optional

from .constants import (
    ACTION_LABEL,
    MAX_RECORDED_ACTIONS,
    Action,
    Phase,
)
from .level import Level
from .position import Pos
from .rules import blocked_reason
from .state import GameState
from .tilemap import TileMap

_DIRECTIONS = (Action.UP, Action.DOWN, Action.LEFT, Action.RIGHT)


# ==========================================================================
# 录制
# ==========================================================================
def record_action(state: GameState, action: Action) -> str:
    """往晶片里追加一个动作；超过上限就拒绝并提示。"""
    if len(state.actions) >= MAX_RECORDED_ACTIONS:
        return (
            "The chip is full ({0}/{0}). "
            "Undo a step or confirm the recording."
        ).format(MAX_RECORDED_ACTIONS)
    state.actions.append(action)
    return "Recorded step {0}: {1}.".format(
        len(state.actions), ACTION_LABEL[action]
    )


def undo_action(state: GameState) -> str:
    """撤销最后一个动作。"""
    if not state.actions:
        return "There is nothing recorded yet."
    removed = state.actions.pop()
    return "Removed step {0}: {1}.".format(
        len(state.actions) + 1, ACTION_LABEL[removed]
    )


def clear_actions(state: GameState) -> str:
    """清空录制（重新录一段）。"""
    if not state.actions:
        return "The chip is already empty."
    state.actions = []
    return "The chip is erased. Start again."


def commit_recording(state: GameState) -> str:
    """确认录制。确认后动作列表就冻结，直到下一次重新录制。"""
    if not state.actions:
        return (
            "Nothing is recorded. Add at least one step before confirming."
        )
    return (
        "Recording frozen at {0} step(s). "
        "Use the console to reset the room."
    ).format(len(state.actions))


# ==========================================================================
# 重置与回声
# ==========================================================================
def can_project_echo(state: GameState) -> bool:
    """能否开始一轮执行：装置可用 且 至少录了一个动作。"""
    return state.device_ready() and len(state.actions) > 0


def _nearest_free_tile(
    level: Level,
    tilemap: TileMap,
    state: GameState,
    start: Pos,
    forbidden: set,
) -> Pos:
    """从 start 开始做广度优先搜索，找出最近的、可以站人的格子。

    重置时回声会占据入口格，玩家必须让到旁边；
    用 BFS 而不是写死坐标，以后改地图也不会出问题。
    """
    seen = {start}
    queue = deque([start])
    while queue:
        pos = queue.popleft()
        if pos not in forbidden and blocked_reason(tilemap, state, pos) is None:
            return pos
        for action in _DIRECTIONS:
            nxt = pos.neighbour(action)
            if nxt in seen:
                continue
            if not tilemap.in_bounds(nxt) or tilemap.is_wall(nxt):
                continue
            seen.add(nxt)
            queue.append(nxt)
    # 理论上不可能走到这里；保底返回起点
    return start


def reset_room(
    level: Level,
    tilemap: TileMap,
    state: GameState,
    project_echo: bool = False,
) -> str:
    """把房间实体恢复成初始样子。

    project_echo=False -> 只是"重新开始房间"（探索阶段，玩家回到入口）；
    project_echo=True  -> 在执行"重置装置"：投影回声并进入执行阶段。

    无论哪种，动作列表和装置知识都保留（它们不在房间快照里）。
    """
    # 1) 房间实体复原
    state.box = level.box_start
    state.door_open = False
    state.win = False
    state.turn = 0
    state.phase = Phase.EXPLORE

    # 2) 回声
    if project_echo:
        state.echo = level.echo_start
        state.echo_index = 0
        state.phase = Phase.EXECUTE
        state.attempt += 1
    else:
        state.echo = None
        state.echo_index = 0

    # 3) 玩家回到入口；若入口被回声占了，就退到最近的空格
    forbidden = {state.echo} if state.echo is not None else set()
    if level.player_start in forbidden:
        state.player = _nearest_free_tile(
            level, tilemap, state, level.player_start, forbidden
        )
    else:
        state.player = level.player_start

    if project_echo:
        return (
            "The room resets. Your echo appears at the entrance, "
            "holding {0} recorded step(s)."
        ).format(len(state.actions))
    return "The room resets. The crate is back on its mark."


def start_new_game(level: Level) -> GameState:
    """完全重开一局（清空录制与装置知识）。"""
    return GameState.new(level)
