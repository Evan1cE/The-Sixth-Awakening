#!/usr/bin/env python3
"""第六次醒来 / The Sixth Awakening —— 程序入口。

运行方式（在项目根目录）：
    python main.py

课程 Docker 容器内：
    docker run --rm -it -v "$PWD":/project engg1330-project:2026-v03 \
        python /project/main.py

整个游戏只依赖 Python 标准库，不需要额外安装任何包。
"""

import sys

from game.engine import main

if __name__ == "__main__":
    sys.exit(main())
