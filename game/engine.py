"""游戏主循环：读指令 -> 改状态 -> 重画。

这里负责"阶段切换"和"界面叠加层"，具体规则都交给 rules / recorder。
这样以后要换界面（例如加颜色或换成别的前端）只要替换 render 即可。
"""

import sys
from typing import List, Optional

from . import recorder, render, rules, screen
from .constants import MAX_RECORDED_ACTIONS, MOVE_KEYS, Phase
from .level import DEFAULT_LEVEL, Level
from .state import GameState
from .tilemap import TileMap

# 任何界面下都能用的退出指令
QUIT_COMMANDS = ("q", "quit", "exit")


class Game:
    """一局游戏的全部交互状态。"""

    def __init__(self, level: Level = DEFAULT_LEVEL) -> None:
        self.level = level
        self.tilemap = TileMap(level)
        self.state = GameState.new(level)

        # overlay 是"盖在正常画面上的一层界面"，与 state.phase 分开：
        #   None      正常游戏
        #   "title"   开场
        #   "help"    说明
        #   "console" 记录器台菜单
        #   "record"  录制
        #   "win"     通关
        self.overlay: Optional[str] = "title"
        self.help_return: Optional[str] = "title"
        self.feedback: List[str] = []

    # ------------------------------------------------------------------
    # 输出
    # ------------------------------------------------------------------
    def say(self, message: str) -> None:
        """往消息区追加一句话（只保留最近三条，连续重复的会合并）。"""
        if not message:
            return
        if self.feedback and self.feedback[-1] == message:
            return
        self.feedback.append(message)
        del self.feedback[:-3]

    def draw(self) -> None:
        """重画整屏。"""
        frame = render.build(
            self.state, self.level, self.tilemap, self.overlay, self.feedback
        )
        screen.clear()
        sys.stdout.write("\n".join(frame))
        sys.stdout.flush()

    @staticmethod
    def ask(prompt: str = "> ") -> str:
        """读一行输入。读到 EOF 或 Ctrl-C 时当作退出，避免程序崩溃。"""
        try:
            return input(prompt).strip().lower()
        except (EOFError, KeyboardInterrupt):
            return "q"

    # ------------------------------------------------------------------
    # 主循环
    # ------------------------------------------------------------------
    def run(self) -> int:
        while True:
            # 终端比 80x24 小的时候暂停游戏，只显示一条能塞进去的提示
            if not screen.fits():
                screen.show_resize_message()
                if self.ask("") in QUIT_COMMANDS:
                    break
                continue

            self.draw()
            command = self.ask()
            if not self.handle(command):
                break

        print("\nThanks for playing.")
        return 0

    # ------------------------------------------------------------------
    # 指令分发
    # ------------------------------------------------------------------
    def handle(self, command: str) -> bool:
        """处理一条指令；返回 False 表示要退出游戏。"""
        if command in QUIT_COMMANDS:
            return False

        if self.overlay == "title":
            return self._handle_title(command)
        if self.overlay == "help":
            return self._handle_help(command)
        if self.overlay == "win":
            return self._handle_win(command)
        if self.overlay == "console":
            return self._handle_console(command)
        if self.overlay == "record":
            return self._handle_record(command)
        return self._handle_play(command)

    # ------------------------------------------------------------------
    # 各界面
    # ------------------------------------------------------------------
    def _handle_title(self, command: str) -> bool:
        if command in ("", "enter", "start", "p"):
            self.overlay = None
            self.say(
                "The door clicks shut behind you. "
                "A crate, a weight plate, and a recorder that remembers."
            )
        elif command in ("h", "help", "?"):
            self.help_return = "title"
            self.overlay = "help"
        else:
            self.say("Press ENTER to begin, H for instructions, Q to quit.")
        return True

    def _handle_help(self, command: str) -> bool:
        # 说明画面里任意键返回（Q 已经在前面被当成退出处理了）
        self.overlay = self.help_return
        return True

    def _handle_win(self, command: str) -> bool:
        if command in ("p", "play", "again"):
            self.state = GameState.new(self.level)
            self.feedback = []
            self.overlay = None
            self.say("Another night in the archive. The room is as you left it.")
        elif command in ("t", "title"):
            self.overlay = "title"
        else:
            self.say("[P] play again, [Q] quit.")
        return True

    def _handle_play(self, command: str) -> bool:
        if command in ("h", "help", "?"):
            self.help_return = None
            self.overlay = "help"
            return True
        if command in ("r", "restart", "reset"):
            self.say(
                recorder.reset_room(
                    self.level, self.tilemap, self.state, project_echo=False
                )
            )
            return True
        if command in ("e", "use", "interact"):
            self._do_interact()
            return True

        action = MOVE_KEYS.get(command)
        if action is None:
            self.say("Unknown command. Type H for instructions.")
            return True

        if self.state.phase is Phase.EXPLORE:
            self.say(
                rules.step_explore(self.level, self.tilemap, self.state, action)
            )
        elif self.state.phase is Phase.EXECUTE:
            self.say(rules.step_execute(self.level, self.tilemap, self.state, action))
            if self.state.win:
                self.overlay = "win"
        return True

    def _do_interact(self) -> None:
        """处理 E 键。"""
        if self.state.phase is Phase.EXECUTE:
            self.say(
                "The console only answers between awakenings. "
                "Press R to restore the room first."
            )
            return

        kind, message = rules.interact(self.level, self.state)
        self.say(message)
        if kind == "console":
            self.overlay = "console"

    # ------------------------------------------------------------------
    # 记录器台
    # ------------------------------------------------------------------
    def _handle_console(self, command: str) -> bool:
        if command in ("1", "record", "edit"):
            self.overlay = "record"
            self.say(
                "The chip is open. {0} slots.".format(MAX_RECORDED_ACTIONS)
            )
            return True

        if command in ("2", "reset", "project"):
            if not recorder.can_project_echo(self.state):
                self.say(
                    "The console will not reset yet. "
                    "Record at least one step first."
                )
                return True
            self.say(
                recorder.reset_room(
                    self.level, self.tilemap, self.state, project_echo=True
                )
            )
            self.overlay = None
            return True

        if command in ("3", "b", "back"):
            self.overlay = None
            self.say("You step away from the console.")
            return True

        # 允许在菜单里直接按方向键查看，但不会推进回合
        self.say("Choose 1, 2 or 3.")
        return True

    # ------------------------------------------------------------------
    # 录制
    # ------------------------------------------------------------------
    def _handle_record(self, command: str) -> bool:
        if command in ("c", "confirm", "done"):
            message = recorder.commit_recording(self.state)
            self.say(message)
            if self.state.actions:
                self.overlay = "console"
            return True

        if command in ("u", "undo"):
            self.say(recorder.undo_action(self.state))
            return True

        if command in ("b", "back", "cancel"):
            self.overlay = "console"
            self.say("You close the chip.")
            return True

        action = MOVE_KEYS.get(command)
        if action is None:
            self.say("Use W/A/S/D/X to add, U undo, C confirm, B back.")
            return True

        self.say(recorder.record_action(self.state, action))
        return True


def main() -> int:
    """程序入口（main.py 只是调用它）。"""
    try:
        return Game().run()
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 0
