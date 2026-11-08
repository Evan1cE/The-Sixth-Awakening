"""终端辅助：清屏、尺寸检测、终端过小时的提示。

课程要求所有绘制都必须落在 80 x 24 之内；如果终端比这个还小，
游戏必须暂停并显示一个能塞进当前窗口的提示。
"""

import os
import shutil
import sys

from .constants import SCREEN_HEIGHT, SCREEN_WIDTH


def is_tty() -> bool:
    """判断标准输出是否连着真正的终端（管道 / 重定向时返回 False）。"""
    try:
        return sys.stdout.isatty()
    except Exception:
        return False


def terminal_size():
    """返回 (列数, 行数)。

    shutil.get_terminal_size 在拿不到真实尺寸时会用 fallback，
    所以这里不会抛异常，非交互环境也能正常跑（自动化测试会用到）。
    """
    try:
        size = shutil.get_terminal_size(fallback=(SCREEN_WIDTH, SCREEN_HEIGHT))
        return size.columns, size.lines
    except Exception:
        return SCREEN_WIDTH, SCREEN_HEIGHT


def fits() -> bool:
    """终端是否够大（至少 80 x 24）。"""
    cols, lines = terminal_size()
    return cols >= SCREEN_WIDTH and lines >= SCREEN_HEIGHT


def clear() -> None:
    """清屏。

    非终端环境（被重定向到文件 / 管道）时直接跳过，
    这样自动测试抓到的输出才是干净的纯文本。
    """
    if not is_tty():
        return
    if os.name == "nt":
        # Windows 的控制台不支持通用的 ANSI 序列时，cls 最稳
        os.system("cls")
    else:
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.flush()


def show_resize_message() -> None:
    """终端过小的时候显示提示，内容会裁剪到当前窗口大小。"""
    cols, lines = terminal_size()
    message = [
        "Terminal too small.",
        "This game needs {0} x {1}.".format(SCREEN_WIDTH, SCREEN_HEIGHT),
        "Current size: {0} x {1}.".format(cols, lines),
        "",
        "Resize the window, then press ENTER.",
        "Press Q to quit.",
    ]
    sys.stdout.write("\n".join(line[:cols] for line in message[:lines]))
    sys.stdout.flush()
