"""界面渲染：把游戏状态画成一整屏 80 x 24 的字符画面。

本模块只读状态、不改状态（对应设计文档第九节的 Renderer 职责）。
build() 永远返回 24 个字符串，每个不超过 80 列，
所以上层只要把它们按行打印，就一定不会越过课程要求的终端区域。
"""

import textwrap
from typing import List, Sequence

from .constants import (
    ACTION_SHORT,
    FLOOR,
    MAX_RECORDED_ACTIONS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TILE_RECORDER,
    Phase,
)
from .level import Level
from .position import Pos
from .state import GameState
from .tilemap import TileMap

INNER_WIDTH = SCREEN_WIDTH - 4      # 边框内可用宽度 = 76

# 固定行号：改版面时只改这里，其它地方不用记住数字
ROW_TITLE = 1
ROW_STATUS = 3
ROW_MAP_TOP = 6
ROW_SLOTS = 14
ROW_RULE_4 = 15
ROW_LEGEND_1 = 16
ROW_LEGEND_2 = 17
ROW_RULE_5 = 18
ROW_PANEL = 19           # 控制台 / 录制面板的第一行
ROW_FEEDBACK_TOP = 20    # 普通画面里消息区的第一行


# ==========================================================================
# 小工具
# ==========================================================================
def _border(fill: str = "=") -> str:
    """画一条 80 列的分隔线。"""
    return "+" + fill * (SCREEN_WIDTH - 2) + "+"


def _row(text: str = "") -> str:
    """画一行带左右竖线的内容行，自动补齐到 80 列。"""
    return "| " + text[:INNER_WIDTH].ljust(INNER_WIDTH) + " |"


def _row_pair(left: str, right: str) -> str:
    """一行里左对齐一段、右对齐一段。"""
    gap = INNER_WIDTH - len(left) - len(right)
    if gap < 1:
        gap = 1
    return _row(left + " " * gap + right)


def _pad(frame: Sequence[str]) -> List[str]:
    """把画面裁剪 / 补齐到正好 24 行、每行不超过 80 列。"""
    lines = [line[:SCREEN_WIDTH] for line in frame][:SCREEN_HEIGHT]
    while len(lines) < SCREEN_HEIGHT:
        lines.append("")
    return lines


# ==========================================================================
# 主入口
# ==========================================================================
def build(
    state: GameState,
    level: Level,
    tilemap: TileMap,
    overlay: str,
    feedback: Sequence[str],
) -> List[str]:
    """根据状态生成一整屏画面。

    overlay 表示当前叠加的界面层：
        "title"    开场画面
        "help"     操作说明
        "win"      通关画面
        "console"  记录器台菜单
        "record"   录制动作
        None       正常游戏画面
    """
    if overlay == "title":
        return _title_frame()
    if overlay == "help":
        return _help_frame()
    if overlay == "win" or state.phase is Phase.WIN:
        return _win_frame(state)

    lines = [""] * SCREEN_HEIGHT
    _draw_header(lines, state, overlay)
    _draw_map_block(lines, state, level, tilemap)
    _draw_slots(lines, state)
    _draw_legend(lines)

    if overlay == "console":
        _draw_console_panel(lines, state, feedback)
    elif overlay == "record":
        _draw_record_panel(lines, state, feedback)
    else:
        _draw_feedback(lines, feedback)
    return lines


# ==========================================================================
# 各区块
# ==========================================================================
def _draw_header(lines: List[str], state: GameState, overlay: str) -> None:
    """标题栏 + 状态栏。"""
    lines[0] = _border("=")
    lines[ROW_TITLE] = _row_pair(
        "  THE SIXTH AWAKENING",
        "awakening {0}  ".format(state.attempt),
    )
    lines[2] = _border("=")

    # 正在录制 / 正在看菜单时，阶段文字也要跟着变，避免玩家困惑
    if overlay == "record":
        phase_name = "Recording"
    elif overlay == "console":
        phase_name = "Console"
    else:
        phase_name = state.phase.value.title()

    lines[ROW_STATUS] = _row_pair(
        "  Phase: {0}".format(phase_name),
        "Turn {0}  ".format(state.turn),
    )
    lines[4] = _border("-")


def _draw_map_block(
    lines: List[str], state: GameState, level: Level, tilemap: TileMap
) -> None:
    """左边画地图，右边画状态面板。"""
    panel = _status_panel(state, level)
    for y in range(tilemap.height):
        map_row = _map_row(state, tilemap, y)
        side = panel[y] if y < len(panel) else ""
        # 3 格缩进 + 9 格地图 + 5 格空隙 = 面板从第 17 列开始
        lines[ROW_MAP_TOP + y] = ("   " + map_row + "     " + side)[:SCREEN_WIDTH]


def _map_row(state: GameState, tilemap: TileMap, y: int) -> str:
    """画出地图的第 y 行。动态对象的优先级：回声 > 玩家 > 木箱 > 地形。"""
    cells = []
    for x in range(tilemap.width):
        pos = Pos(x, y)
        if state.echo is not None and pos == state.echo:
            cells.append("o")
        elif pos == state.player:
            cells.append("P")
        elif pos == state.box:
            cells.append("C")
        else:
            tile = tilemap.tile(pos)
            # 晶片被取走后，那一格就恢复成普通地板，不要再画 R
            if tile == TILE_RECORDER and state.recorder_taken:
                tile = FLOOR
            cells.append(tile)
    return "".join(cells)


def _status_panel(state: GameState, level: Level) -> List[str]:
    """地图右侧的七行状态说明（正好和 7 行地图对齐）。"""
    left_on, right_on = state.exit_plates_pressed(level)
    return [
        "DEVICE   : " + ("online" if state.device_ready() else "locked"),
        "RECORDER : " + ("carried" if state.recorder_taken else "on the wall"),
        "WEIGHT A : " + ("pressed" if state.plate_a_pressed(level) else "up"),
        "EXIT B   : " + ("pressed" if left_on else "clear"),
        "EXIT E   : " + ("pressed" if right_on else "clear"),
        "DOOR     : " + ("OPEN" if state.door_open else "sealed"),
        "ECHO     : " + ("projected" if state.echo is not None else "-"),
    ]


def _draw_slots(lines: List[str], state: GameState) -> None:
    """显示晶片里的五个动作槽。"""
    cells = []
    for index in range(MAX_RECORDED_ACTIONS):
        if index < len(state.actions):
            cells.append("[" + ACTION_SHORT[state.actions[index]] + "]")
        else:
            cells.append("[ ]")
    lines[ROW_SLOTS] = ("  RECORDED : " + " ".join(cells))[:SCREEN_WIDTH]


def _draw_legend(lines: List[str]) -> None:
    """图例。两行刚好放下所有符号。"""
    lines[ROW_RULE_4] = _border("-")
    lines[ROW_LEGEND_1] = "  # wall   . floor   P you   o echo   C crate   A weight plate"
    lines[ROW_LEGEND_2] = "  B / E exit plates   R recorder   D console   G exit"
    lines[ROW_RULE_5] = _border("-")


def _draw_feedback(lines: List[str], feedback: Sequence[str]) -> None:
    """消息区：显示最近一两句反馈。"""
    text = " ".join(feedback[-2:]) if feedback else ""
    if not text:
        return
    wrapped = textwrap.wrap(text, width=INNER_WIDTH - 6)
    for offset, line in enumerate(wrapped[:3]):
        lines[ROW_FEEDBACK_TOP + offset] = ("  " + line)[:SCREEN_WIDTH]


def _draw_console_panel(
    lines: List[str], state: GameState, feedback: Sequence[str]
) -> None:
    """记录器台菜单（编号选择，符合课程说明里"编号选项即可"的要求）。"""
    lines[ROW_PANEL] = ("  " + (feedback[-1] if feedback else "The console waits."))[
        :SCREEN_WIDTH
    ]
    lines[20] = "  [1]  Edit the recorded actions"
    lines[21] = "  [2]  Reset the room and project the echo   ({0} step(s))".format(
        len(state.actions)
    )
    lines[22] = "  [3]  Step away                     (Q quits the game)"


def _draw_record_panel(
    lines: List[str], state: GameState, feedback: Sequence[str]
) -> None:
    """录制面板：显示按键、已用槽数和小提示。"""
    lines[ROW_PANEL] = ("  " + (feedback[-1] if feedback else "The chip is blank."))[
        :SCREEN_WIDTH
    ]
    lines[20] = "  W/A/S/D add a step    X wait    U undo    C confirm    B back"
    lines[21] = "  Slots used: {0}/{1}".format(
        len(state.actions), MAX_RECORDED_ACTIONS
    )
    lines[22] = "  Typing is only a plan: nothing in the room moves yet."


# ==========================================================================
# 独立画面
# ==========================================================================
def _title_frame() -> List[str]:
    """开场画面：交代故事、目标和操作。"""
    frame = [
        _border("="),
        _row(""),
        _row("                T H E   S I X T H   A W A K E N I N G"),
        _row(""),
        _border("="),
        _row(""),
        _row("  Closing time. The underground archive has sealed itself, and"),
        _row("  the calibration device keeps returning the room to its first"),
        _row("  state. The recorder in the corner still remembers five actions."),
        _row("  If you reset, the you of this round will walk those steps again."),
        _row(""),
        _row('  "I cannot decide for you, but I can walk that road once more."'),
        _row(""),
        _border("="),
        _row(""),
        _row("  GOAL   press both exit plates at the same time, then reach G."),
        _row(""),
        _row("  MOVE   W up   A left   S down   D right   X wait"),
        _row("  ACT    E interact   R restore room   H instructions   Q quit"),
        _row(""),
        _border("="),
        _row(""),
        _row("  Press ENTER to begin."),
        "",
    ]
    return _pad(frame)


def _help_frame() -> List[str]:
    """操作说明画面。"""
    frame = [
        _border("="),
        _row("  HOW TO PLAY"),
        _border("="),
        _row(""),
        _row("  You are Lin Che, an archivist locked in a room that keeps"),
        _row("  resetting itself. A recorder can hold five of your actions."),
        _row("  After a reset, the echo of your past self repeats them step"),
        _row("  by step while you act again."),
        _row(""),
        _row("  GOAL   both exit plates pressed at once, then reach G."),
        _row(""),
        _row("  1  Push the crate C onto the weight plate A (walk into it)."),
        _row("  2  Stand next to the recorder R and press E to take it."),
        _row("  3  Stand next to the console D, press E, record up to 5 steps."),
        _row("  4  Choose [2] to reset the room and project your echo."),
        _row("  5  The echo holds one plate; you take the other, then reach G."),
        _row(""),
        _row("  MOVE   W up   A left   S down   D right   X wait"),
        _row("  ACT    E interact   R restore room   H help   Q quit"),
        _row("  NOTE   a blocked step still costs a turn for both of you."),
        _border("="),
        _row(""),
        _row("  Press ENTER to go back."),
    ]
    return _pad(frame)


def _win_frame(state: GameState) -> List[str]:
    """通关画面。"""
    frame = [
        _border("="),
        _row(""),
        _row("                     V I C T O R Y"),
        _row(""),
        _border("="),
        _row(""),
        _row("  You step through the door, and the room lets go of you."),
        _row(""),
        _row('  "Twice awake, and at last before the same door."'),
        _row(""),
        _border("-"),
        _row(""),
        _row("  Awakenings : {0}".format(state.attempt)),
        _row("  Turns      : {0}".format(state.turn)),
        _row(
            "  Recorded by your past self : {0} step(s)".format(
                len(state.actions)
            )
        ),
        _row(""),
        _border("="),
        _row(""),
        _row("  [P] play again      [Q] quit"),
        _row(""),
        "",
    ]
    return _pad(frame)
