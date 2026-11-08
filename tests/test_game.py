"""第六次醒来的规则测试。

运行方式（在项目根目录）：
    python -m unittest discover -s tests -v

这些测试只调用 rules / recorder 两个模块，不需要终端，
所以可以在课程容器里、CI 里或随便哪台机器上跑。
"""

import os
import sys
import unittest

# 让测试文件无论从哪里被调用都能 import 到 game 包
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from game import recorder, render, rules                       # noqa: E402
from game.constants import (                                    # noqa: E402
    MAX_RECORDED_ACTIONS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    Action,
    Phase,
)
from game.level import DEFAULT_LEVEL                            # noqa: E402
from game.position import Pos                                   # noqa: E402
from game.state import GameState                                # noqa: E402
from game.tilemap import TileMap                                # noqa: E402


def make_game():
    """每个测试都拿到一份干净的地图与状态。"""
    level = DEFAULT_LEVEL
    return level, TileMap(level), GameState.new(level)


class TestMovement(unittest.TestCase):
    """地图与移动。"""

    def test_wall_blocks_player(self):
        level, tilemap, state = make_game()
        # (1,3) 往左是墙 (0,3)
        rules.step_explore(level, tilemap, state, Action.LEFT)
        self.assertEqual(state.player, Pos(1, 3))

    def test_open_floor_allows_movement(self):
        level, tilemap, state = make_game()
        rules.step_explore(level, tilemap, state, Action.UP)
        self.assertEqual(state.player, Pos(1, 2))

    def test_console_cannot_be_walked_into(self):
        level, tilemap, state = make_game()
        state.player = Pos(4, 2)          # 控制台 (4,3) 的正上方
        rules.step_explore(level, tilemap, state, Action.DOWN)
        self.assertEqual(state.player, Pos(4, 2))


class TestCrate(unittest.TestCase):
    """推箱与配重板。"""

    def test_push_crate(self):
        level, tilemap, state = make_game()
        state.player = Pos(2, 2)          # 箱子左边的空格
        rules.step_explore(level, tilemap, state, Action.RIGHT)
        self.assertEqual(state.box, Pos(4, 2))
        self.assertEqual(state.player, Pos(3, 2))

    def test_push_crate_into_wall_fails(self):
        level, tilemap, state = make_game()
        # 箱子在 (7,1)，右边 (8,1) 是墙，推不动
        state.box = Pos(7, 1)
        state.player = Pos(6, 1)
        rules.step_explore(level, tilemap, state, Action.RIGHT)
        self.assertEqual(state.box, Pos(7, 1))
        self.assertEqual(state.player, Pos(6, 1))

    def test_crate_on_plate_powers_console(self):
        level, tilemap, state = make_game()
        state.box = Pos(5, 2)
        state.player = Pos(4, 2)
        rules.step_explore(level, tilemap, state, Action.RIGHT)
        self.assertEqual(state.box, level.weight_plate)
        self.assertTrue(state.plate_a_pressed(level))


class TestRecorder(unittest.TestCase):
    """晶片拾取、录制上限、装置解锁条件。"""

    def test_pickup_requires_adjacency(self):
        level, tilemap, state = make_game()
        kind, _ = rules.interact(level, state)      # 起点 (1,3) 离晶片 (3,1) 很远
        self.assertEqual(kind, "nothing")
        self.assertFalse(state.recorder_taken)

    def test_pickup_adjacent(self):
        level, tilemap, state = make_game()
        state.player = Pos(4, 1)
        kind, _ = rules.interact(level, state)
        self.assertEqual(kind, "pickup")
        self.assertTrue(state.recorder_taken)

    def test_device_needs_power_and_recorder(self):
        level, tilemap, state = make_game()
        state.player = Pos(4, 1)
        rules.interact(level, state)                 # 只是取了晶片
        self.assertFalse(state.device_ready())       # 还没通电
        state.power_ever = True
        self.assertTrue(state.device_ready())

    def test_recording_cap(self):
        level, tilemap, state = make_game()
        for _ in range(MAX_RECORDED_ACTIONS):
            recorder.record_action(state, Action.RIGHT)
        self.assertEqual(len(state.actions), MAX_RECORDED_ACTIONS)
        recorder.record_action(state, Action.LEFT)   # 第 6 个必须被拒绝
        self.assertEqual(len(state.actions), MAX_RECORDED_ACTIONS)

    def test_undo(self):
        level, tilemap, state = make_game()
        recorder.record_action(state, Action.UP)
        recorder.undo_action(state)
        self.assertEqual(state.actions, [])

    def test_cannot_project_without_recording(self):
        level, tilemap, state = make_game()
        state.power_ever = True
        state.recorder_taken = True
        self.assertFalse(recorder.can_project_echo(state))


class TestReset(unittest.TestCase):
    """重置只复原房间实体，不抹掉录制与装置知识。"""

    def test_reset_restores_crate_and_keeps_recording(self):
        level, tilemap, state = make_game()
        state.box = Pos(6, 2)
        state.recorder_taken = True
        state.power_ever = True
        recorder.record_action(state, Action.RIGHT)

        recorder.reset_room(level, tilemap, state, project_echo=False)

        self.assertEqual(state.box, level.box_start)     # 箱子回到原位
        self.assertEqual(state.player, level.player_start)
        self.assertEqual(len(state.actions), 1)          # 录制保留
        self.assertTrue(state.recorder_taken)            # 装置知识保留
        self.assertIsNone(state.echo)
        self.assertEqual(state.phase, Phase.EXPLORE)

    def test_reset_never_overlaps_echo_and_player(self):
        level, tilemap, state = make_game()
        recorder.reset_room(level, tilemap, state, project_echo=True)
        self.assertIsNotNone(state.echo)
        self.assertNotEqual(state.player, state.echo)
        self.assertEqual(state.phase, Phase.EXECUTE)


class TestEcho(unittest.TestCase):
    """回声重放与双方冲突。"""

    def test_echo_follows_recording(self):
        level, tilemap, state = make_game()
        state.actions = [Action.RIGHT, Action.RIGHT, Action.DOWN]
        recorder.reset_room(level, tilemap, state, project_echo=True)

        rules.step_execute(level, tilemap, state, Action.WAIT)
        self.assertEqual(state.echo, Pos(2, 3))
        rules.step_execute(level, tilemap, state, Action.WAIT)
        self.assertEqual(state.echo, Pos(3, 3))
        rules.step_execute(level, tilemap, state, Action.WAIT)
        self.assertEqual(state.echo, Pos(3, 4))            # 站上左压力板 B

    def test_echo_waits_after_list_ends(self):
        level, tilemap, state = make_game()
        state.actions = [Action.RIGHT]
        recorder.reset_room(level, tilemap, state, project_echo=True)
        for _ in range(5):
            rules.step_execute(level, tilemap, state, Action.WAIT)
        self.assertEqual(state.echo, Pos(2, 3))            # 停在原地等

    def test_blocked_echo_still_consumes_turn(self):
        level, tilemap, state = make_game()
        state.actions = [Action.UP, Action.UP, Action.UP]
        recorder.reset_room(level, tilemap, state, project_echo=True)
        state.player = Pos(5, 5)       # 先把玩家挪开，只观察回声
        rules.step_execute(level, tilemap, state, Action.WAIT)   # -> (1,2)
        rules.step_execute(level, tilemap, state, Action.WAIT)   # -> (1,1)
        rules.step_execute(level, tilemap, state, Action.WAIT)   # 撞墙，停住
        self.assertEqual(state.echo, Pos(1, 1))
        self.assertEqual(state.echo_index, 3)                    # 动作仍被消耗

    def test_player_cannot_step_onto_echo(self):
        level, tilemap, state = make_game()
        state.player = Pos(1, 3)
        state.echo = Pos(2, 3)
        rules.step_execute(level, tilemap, state, Action.RIGHT)
        self.assertEqual(state.player, Pos(1, 3))

    def test_swap_is_refused(self):
        level, tilemap, state = make_game()
        # 玩家 (2,3) 想往左，回声 (1,3) 想往右 —— 会交换位置，必须都停住
        state.player = Pos(2, 3)
        state.echo = Pos(1, 3)
        state.actions = [Action.RIGHT]
        state.echo_index = 0
        rules.step_execute(level, tilemap, state, Action.LEFT)
        self.assertEqual(state.player, Pos(2, 3))
        self.assertEqual(state.echo, Pos(1, 3))


class TestExit(unittest.TestCase):
    """双板、开门与通关。"""

    def test_both_plates_open_door(self):
        level, tilemap, state = make_game()
        state.player = level.exit_plates[0]
        state.echo = level.exit_plates[1]
        state.actions = [Action.WAIT]
        rules.step_execute(level, tilemap, state, Action.WAIT)
        self.assertTrue(state.door_open)

    def test_door_stays_open_after_leaving_plate(self):
        level, tilemap, state = make_game()
        state.player = level.exit_plates[0]
        state.echo = level.exit_plates[1]
        state.actions = [Action.WAIT]
        rules.step_execute(level, tilemap, state, Action.WAIT)
        self.assertTrue(state.door_open)
        # 玩家离开压力板，门仍然保持开启
        rules.step_execute(level, tilemap, state, Action.DOWN)
        self.assertNotEqual(state.player, level.exit_plates[0])
        self.assertTrue(state.door_open)

    def test_no_win_while_door_is_closed(self):
        level, tilemap, state = make_game()
        state.player = level.exit_tile
        self.assertFalse(rules.check_win(level, state))

    def test_win_when_door_open_and_player_on_exit(self):
        level, tilemap, state = make_game()
        state.door_open = True
        state.player = level.exit_tile
        self.assertTrue(rules.check_win(level, state))
        self.assertEqual(state.phase, Phase.WIN)


class TestFullPlaythrough(unittest.TestCase):
    """完整通关：推箱 -> 取晶片 -> 录 5 步 -> 重置 -> 双板 -> 出口。"""

    def test_solve_the_room(self):
        level, tilemap, state = make_game()

        # --- 探索：把箱子推到配重板 A (6,2) ---
        for action in (
            Action.UP,      # (1,3) -> (1,2)
            Action.RIGHT,   # -> (2,2)
            Action.RIGHT,   # 推箱 (3,2) -> (4,2)
            Action.RIGHT,   # 推箱 -> (5,2)
            Action.RIGHT,   # 推箱 -> (6,2) = A
        ):
            rules.step_explore(level, tilemap, state, action)
        self.assertEqual(state.box, level.weight_plate)
        self.assertTrue(state.power_ever)

        # --- 取晶片并走到控制台旁边 ---
        rules.step_explore(level, tilemap, state, Action.UP)     # (5,1)
        rules.step_explore(level, tilemap, state, Action.LEFT)   # (4,1)
        kind, _ = rules.interact(level, state)                   # 取晶片
        self.assertEqual(kind, "pickup")
        rules.step_explore(level, tilemap, state, Action.DOWN)   # (4,2)
        kind, _ = rules.interact(level, state)                   # 控制台可用
        self.assertEqual(kind, "console")

        # --- 录下五步，然后重置并投影回声 ---
        for action in (
            Action.RIGHT,
            Action.RIGHT,
            Action.DOWN,
            Action.WAIT,
            Action.WAIT,
        ):
            recorder.record_action(state, action)
        self.assertTrue(recorder.can_project_echo(state))
        recorder.reset_room(level, tilemap, state, project_echo=True)
        self.assertEqual(state.phase, Phase.EXECUTE)

        # --- 玩家绕上方通道去右压力板 E，回声去左压力板 B ---
        route = (
            Action.UP,      # (1,2) -> (1,1)
            Action.RIGHT,
            Action.RIGHT,
            Action.RIGHT,
            Action.RIGHT,   # (5,1)
            Action.DOWN,    # (5,2)
            Action.DOWN,    # (5,3)
            Action.DOWN,    # (5,4)
            Action.RIGHT,   # (6,4) = E，此时双板同时被占，门开启
        )
        for action in route:
            rules.step_execute(level, tilemap, state, action)
            self.assertNotEqual(state.player, state.echo)   # 任何时刻都不重叠
        self.assertEqual(state.echo, level.exit_plates[0])
        self.assertEqual(state.player, level.exit_plates[1])
        self.assertTrue(state.door_open)

        # --- 走向出口 ---
        for action in (Action.LEFT, Action.LEFT, Action.DOWN):
            rules.step_execute(level, tilemap, state, action)
        self.assertEqual(state.player, level.exit_tile)
        self.assertTrue(state.win)
        self.assertEqual(state.phase, Phase.WIN)


class TestScreenBudget(unittest.TestCase):
    """课程要求：任何画面都不能超出 80 x 24。"""

    def test_every_frame_fits(self):
        level, tilemap, state = make_game()
        state.actions = [Action.RIGHT, Action.WAIT]
        for overlay in (None, "title", "help", "console", "record", "win"):
            frame = render.build(state, level, tilemap, overlay, ["test message"])
            self.assertEqual(len(frame), SCREEN_HEIGHT)
            for line in frame:
                self.assertLessEqual(len(line), SCREEN_WIDTH)

    def test_last_row_is_free_for_the_prompt(self):
        """第 24 行必须是空的，否则输入提示 "> " 会折行跑出 24 行区域。"""
        level, tilemap, state = make_game()
        for overlay in (None, "title", "help", "console", "record", "win"):
            frame = render.build(state, level, tilemap, overlay, ["test message"])
            self.assertEqual(frame[-1], "", "overlay {0!r} fills the last row".format(overlay))

    def test_map_is_nine_by_seven(self):
        level, tilemap, state = make_game()
        self.assertEqual(level.width, 9)
        self.assertEqual(level.height, 7)


if __name__ == "__main__":
    unittest.main()
