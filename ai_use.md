# AI use declaration — The Sixth Awakening

**Group 1N, ENGG1330 Group Project 2026–27**

## What AI was used for

An AI assistant (DeepSeek) was used during development for:

1. **First-draft code.** Translating the group's design document
   (*第六次醒来*, v1.0) into the Python module layout, the turn-resolution
   function, the renderer and the unit-test skeleton.
2. **Review.** Reading the course brief and submission guidelines and turning
   the constraints (standard library only, 80x24 terminal area, container
   compatibility, `main.py` entry point) into concrete code requirements.
3. **Documentation.** Drafting this README and `ai_use.md`.

AI was **not** used to generate the game design, the room layout, the puzzle
solution or any asset. Those come from the group's own design document.

## How the suggestions were checked

Every rule the AI produced was verified against the design document before it
was accepted:

* **Written specification first.** Rules were compared one by one with sections
  5–8 of the design document: five-action limit, blocked actions still costing a
  turn, no overlap / no swapping, plates derived from occupancy, latched door,
  reset keeping the recording but restoring the room.
* **Read and rewritten.** Each module was read line by line; comments and names
  were changed where they did not match the group's terminology, and the
  collision rules were rewritten after the first version allowed the player and
  the echo to occupy the same tile.
* **Automated tests.** 26 unit tests in `tests/test_game.py` encode the expected
  behaviour, including the boundary cases from section 10 of the design document
  (pushing into a wall, recording 0/5/6 actions, blocked echo, swap refusal,
  door latching, full playthrough). The AI's first draft failed one of them
  (an echo blocked by the player still moved); the test caught it and the
  behaviour was fixed to match the design.
* **Manual playthrough.** The whole puzzle was played in a terminal several
  times, including wrong actions, a full reset, and quitting mid-recording.
* **Screen budget.** A test asserts that every screen overlay is exactly 24
  lines and no line exceeds 80 characters, because the brief treats the terminal
  area as a hard requirement.

## What the group is responsible for

The group understands and can explain every part of the submitted code. If the
AI-authored draft is kept, members will be able to describe:

* why the turn is resolved by computing both intentions before writing positions;
* why switch state is derived from occupancy instead of stored counters;
* why reset keeps the recording and the powered-console flag but restores the
  crate and the player.

No paid tools were used. No code, data or asset was copied from an external
source; see the acknowledgements in `README.md`.
