# The Sixth Awakening (第六次醒来)

**ENGG1330 Group Project — Group 1N**

A single-player, turn-based console puzzle adventure, written in Python with the
standard library only. It runs offline in a terminal and keeps every drawing,
message and input inside an 80-column by 24-row area.

---

## 1. What the game is

Closing time. An archivist is locked inside a self-resetting archive room. The
room holds a crate, a weight plate, a recorder that can store **five actions**,
two pressure plates and a sealed exit. The calibration device resets every
object — but not the recorder's chip.

The player powers the console, records a short route, then resets the room.
The recording is replayed by an **echo** of the previous round. The player and
the echo must press both exit plates **at the same time** to lock the door open,
then walk out.

Two connected puzzles:

1. **Power puzzle** — push the crate onto the weight plate to power the console.
   Solving it unlocks the recorder interaction (it changes what the player can
   do next).
2. **Echo puzzle** — record up to five actions, reset, and split the two plates
   between the echo and the current self.

A full playthrough is about 5–10 minutes.

---

## 2. How to run

### In the course container (the version that is graded)

```bash
python3 main.py
```

Nothing else is required: no packages, no configuration, no assets.
The game needs an interactive terminal of at least 80 columns by 24 rows.

### On your own machine

Python 3.8 or newer, standard library only:

```bash
python main.py
```

### With Docker

The game only wraps the official course image — no extra packages and no custom
image are submitted. The provided `Dockerfile` builds from
`engg1330-project:2026-v03`:

```bash
docker build -t sixth-awakening .
docker run --rm -it sixth-awakening
```

If the course image is not available locally, build on top of any Python 3 image
instead (the game has no dependencies):

```bash
docker build --build-arg BASE_IMAGE=python:3.12-slim -t sixth-awakening .
docker run --rm -it sixth-awakening
```

`-it` is required: the game reads commands from the terminal.

---

## 3. How to play

| Key | Meaning |
| --- | --- |
| `W` `A` `S` `D` | move up / left / down / right (the words `up`, `left`, `down`, `right` also work) |
| `X` | wait one step |
| `E` | interact (take the recorder, use the console) |
| `R` | restore the room without projecting the echo |
| `H` | instructions |
| `Q` | quit |

Map symbols:

| Symbol | Object |
| --- | --- |
| `#` | wall |
| `.` | floor |
| `P` | you |
| `o` | your echo |
| `C` | crate |
| `A` | weight plate (powers the console) |
| `B` / `E` | exit pressure plates |
| `R` | recorder chip |
| `D` | console / reset device |
| `G` | exit |

### Winning route (spoiler)

<details>
<summary>Click to expand</summary>

1. Move up, right, then push the crate right three times: the crate lands on
   the weight plate and the console gets power.
2. Go up, left, press `E` next to the recorder to take it.
3. Go down next to the console, press `E`, choose `[1]`, and record
   **right, right, down, wait, wait**.
4. Choose `[2]` to reset the room and project the echo.
5. Walk the upper corridor to the right plate: the echo reaches the left plate
   and waits there, so both plates are pressed on the same turn and the door
   locks open.
6. Walk to `G`. Victory should happen in about 12 turns.

</details>

---

## 4. Rules in detail

* **One action per turn.** A turn only advances when the player enters a move.
* **Blocked actions still cost a turn.** Walking into a wall, the crate, the
  console or another character leaves the character in place.
* **The echo replays the recording one step per turn.** When the recording runs
  out, the echo waits where it stands.
* **No overlap and no swapping.** If the player and the echo would land on the
  same tile or swap places, both stay put for that turn.
* **Plates are derived, never accumulated.** After every position update the
  game recomputes which plates are occupied; it does not toggle counters. This
  rules out flickering or stale switch state.
* **The door latches open.** Once both exit plates are occupied on the same
  turn, the door stays open, so the player can leave a plate and walk to `G`.
* **Reset keeps knowledge, not objects.** Resetting restores the player, the
  crate and the door, and clears the echo. The recorded actions and the fact
  that the console is powered are kept, so the player never redoes the same
  busywork.
* **No losing state.** There is no health and no soft lock: `R` restores the
  room at any time, and the console can re-record the chip.

---

## 5. Code structure

```
main.py                  entry point (thin wrapper)
game/
    __init__.py          package description
    constants.py         Action / Phase enums, tile characters, screen size
    position.py          Pos (NamedTuple) and movement helpers
    level.py             the 9x7 room, object coordinates, Level dataclass
    tilemap.py           TileMap: static geometry queries
    state.py             GameState and the reset Snapshot
    rules.py             movement, pushing, simultaneous turn resolution, win check
    recorder.py          recording, undo, commit, reset and echo projection
    render.py            builds one 80x24 frame
    screen.py            terminal clearing and size checks
    engine.py            the game loop and screen overlays
tests/
    test_game.py         26 unit tests for the rules and the screen budget
```

Classes and data types: `Game` (engine, composition root), `GameState`
(dataclass holding all mutable state), `Snapshot` (dataclass used for reset),
`Level` (frozen dataclass), `TileMap`, `Pos` (NamedTuple), and the `Action` /
`Phase` enums. The design uses composition rather than inheritance: there is no
"is-a" relationship between these parts, so a class hierarchy would add
indirection without adding meaning. Each module has one responsibility, which
keeps the rules testable without a terminal.

The turn order is deliberately: compute both intentions → check terrain → resolve
conflicts → write both positions → settle switches. Settling after each character
moves separately would make the plates flicker and could open the door by
accident.

---

## 6. Tests

```bash
python -m unittest discover -s tests -t . -v
```

26 tests cover: walls, pushing (including into a wall), plate power, recorder
pickup distance, the five-step cap, undo, reset semantics (objects restored,
recording kept), echo replay, blocked echo still consuming a turn, overlap and
swap refusal, the two-plate condition, the latched door, the win condition, a
complete scripted playthrough, and the 80x24 screen budget for every overlay.

Manual checks are listed in the design document; the automated suite covers the
same cases.

---

## 7. Known limitations

* One room, one level, one crate. Interior walls are not part of the puzzle yet.
* The recording is a stored list of five moves; there is no branching or
  conditional behaviour in the echo.
* Re-recording discards the previous sequence immediately (the console confirms
  before resetting, but the chip has no undo history beyond one step at a time).
* The terminal-size check cannot detect a resize that happens while the game is
  blocked on input; it is re-checked at the start of every turn.
* No sound, colour or animation — the brief keeps real-time effects out of scope.

---

## 8. Contributions

| Member | Work |
| --- | --- |
| (fill in) | design document, room design, puzzle verification |
| (fill in) | rules and state modules, unit tests |
| (fill in) | rendering, input handling, container checks |
| (fill in) | README, videos, peer review |

Update this table before submission, as required by the brief.

---

## 9. Acknowledgements and sources

* Room layout and mechanic specification: the group's own design document
  *第六次醒来* (v1.0).
* No third-party code, libraries, images, fonts or sound are used. Everything is
  written for this project with the Python standard library.
* The course brief (ENGG1330 Group Project 2026–27) defines the 80x24 terminal
  limit and the container requirement.

---

## 10. AI use

See `ai_use.md`. In short: AI assistance was used to draft the first version of
the code; every rule was then checked against the design document and covered by
the unit tests in `tests/test_game.py`.

---

## 中文说明（给组员）

* 运行：在项目根目录执行 `python main.py`，或按第 2 节用 Docker 运行。
* 代码按模块拆分，每个文件开头都有中文注释说明职责；改规则主要动
  `game/rules.py` 和 `game/recorder.py`，改地图/坐标动 `game/level.py`，
  改界面动 `game/render.py`。
* 想改动作上限：`game/constants.py` 里的 `MAX_RECORDED_ACTIONS`（改完记得重跑
  测试，并确认五步推荐路线仍然可解）。
* 想改通话次数/难度：`game/level.py` 里的 `LEVEL_ROWS`，注意同步 `PLAYER_START`
  等坐标常量。
* 提交前务必在干净容器里解压 ZIP 跑一遍，并替换第 8 节的组员分工。
