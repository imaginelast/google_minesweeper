# Google Minesweeper Bot

A computer-vision-based automation system that plays Google's Minesweeper by continuously interpreting the game board, reasoning about mine locations, and executing mouse actions automatically.

The project evolved from an OCR-based prototype into a faster pixel/color-based vision pipeline, significantly reducing the overhead of reading the game state.

## Overview

The bot operates as a closed-loop system:

```text
        ┌─────────────────────┐
        │   Minesweeper UI    │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  Screen Perception  │
        │                     │
        │ Pixel / Color       │
        │ Classification      │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │   Board Modeling    │
        │                     │
        │ 2D Grid of Game     │
        │ States              │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │  Constraint-Based   │
        │     Reasoning       │
        │                     │
        │ Mine / Safe Move    │
        │ Inference           │
        └──────────┬──────────┘
                   │
                   ▼
        ┌─────────────────────┐
        │    PyAutoGUI        │
        │                     │
        │ Left / Right Click  │
        └──────────┬──────────┘
                   │
                   └──────────────► Updated Game State
                                      │
                                      └───────► Loop
```

Rather than relying on fixed gameplay sequences, the bot repeatedly observes the current board and makes decisions from the state it detects.

---

## Features

* Automated screen-based Minesweeper gameplay
* Computer vision through direct pixel/color classification
* Grid-based board state reconstruction
* Detection of:

  * unrevealed tiles
  * flagged mines
  * revealed numbered tiles
* 8-neighbor board traversal
* Deterministic mine inference
* Deterministic safe-move inference
* Automated left/right mouse interaction
* Automatic board re-evaluation after each round of actions
* Automatic game restart in the optimized implementation
* Original OCR implementation included for comparison
* Optimized non-OCR implementation for faster state recognition

---

## How the Bot Works

### 1. Capture the Game Board

The bot assumes the Minesweeper board occupies a known rectangular region of the screen.

For the Easy board, the implementation uses:

```python
x1, y1 = 728, 449
x2, y2 = 1178, 809

cols = 10
rows = 8
```

The board is therefore modeled as a `10 × 8` grid.

Each tile's position is calculated from the board dimensions rather than individually hardcoding every tile location.

```text
Screen Region
┌─────────────────────────────────────────┐
│ [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]          │
│ [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]          │
│ [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]          │
│                ...                       │
│ [ ][ ][ ][ ][ ][ ][ ][ ][ ][ ]          │
└─────────────────────────────────────────┘
             10 columns × 8 rows
```

The tile size is derived from:

```python
tile_size = (x2 - x1) // cols
```

This allows the bot to convert between grid coordinates `(row, column)` and screen coordinates.

---

## 2. Convert Pixels Into Game States

The optimized implementation does not use OCR to read every number.

Instead, it samples pixels at carefully selected locations inside each tile.

For every tile, the bot checks for several possible visual states.

### Flagged Mine

Flags are identified using the red flag color:

```python
flag_color = (242, 54, 7)
```

If the sampled pixels match the flag color, the tile is represented as a mine flag.

### Unrevealed Tile

Unrevealed tiles are identified using the characteristic green background colors:

```python
tile_color = {
    (162, 209, 73),
    (170, 215, 81)
}
```

This avoids the need to perform OCR on tiles that do not contain useful numerical information.

### Revealed Numbers

Revealed Minesweeper numbers use different colors depending on their value.

The implementation maps RGB colors to their corresponding number:

```python
color_to_num = {
    (229, 194, 159): 0,
    (215, 184, 153): 0,
    (25, 118, 210): 1,
    (56, 142, 60): 2,
    (211, 47, 47): 3,
    (123, 31, 162): 4,
    (128, 0, 0): 5,
    (0, 128, 128): 6,
    (0, 0, 0): 7,
    (128, 128, 128): 8,
}
```

This turns the rendered game board into structured numerical data.

---

## 3. Build an Internal Board Representation

Each tile is converted into a value in a 2D Python list.

The optimized implementation uses:

```text
-1  → unrevealed / unknown tile
 0  → revealed empty tile
1-8 → revealed Minesweeper number
 9  → flagged mine
```

For example:

```text
 1  -1  -1   1   0
 2   3   2  -1   0
-1   9   2  -1   1
-1   3   1   1   0
```

This representation allows the vision system to remain separate from the decision-making logic.

Once the screenshot has been converted into this matrix, the solver no longer needs to reason about pixels. It reasons about the abstract board state.

---

## 4. Analyze Neighboring Tiles

Minesweeper numbers provide constraints on their surrounding eight tiles.

The bot defines the eight possible neighboring directions:

```python
directions = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1)
]
```

For each revealed number, the solver examines every valid neighboring coordinate.

It tracks two things:

```text
unknown_neighbors
flagged_bombs
```

This gives the solver the information required to apply deterministic Minesweeper rules.

---

## 5. Infer Guaranteed Mines

Suppose a tile contains the number `3`.

If the bot detects:

```text
3 flagged mines
0 unknown tiles
```

there is nothing to do.

More importantly, if it detects:

```text
3 total mines required
0 flagged mines
3 unknown neighboring tiles
```

then all three unknown neighbors must be mines.

The implementation checks this using:

```python
if new_board[r][c] - flagged_bombs == len(unknown_neighbors):
```

When the condition is satisfied, the bot:

1. Marks each unknown neighbor as a mine internally.
2. Right-clicks the corresponding screen location.
3. Updates the board representation.

This is a deterministic constraint rather than a guess.

---

## 6. Infer Guaranteed Safe Tiles

The opposite constraint can also be used.

If a number already has all of its required mines flagged, every remaining unknown neighboring tile must be safe.

For example:

```text
Number = 2
Flagged mines = 2
Unknown neighbors = 3
```

Since the required two mines have already been identified, the remaining unknown tiles can safely be revealed.

The implementation checks:

```python
if flagged_bombs == new_board[r][c]:
```

and then left-clicks the remaining unknown neighbors.

---

## 7. Execute Actions

The solver converts grid coordinates back into screen coordinates.

For a tile `(r, c)`:

```python
click_x = x1 + c * tile_size + center
click_y = y1 + r * tile_size + center
```

The bot then uses PyAutoGUI:

```python
pyautogui.leftClick(...)
```

for safe tiles and:

```python
pyautogui.rightClick(...)
```

for mines.

This creates the final stage of the perception → reasoning → action loop.

---

## 8. Re-Synchronize With the Game

After performing its actions, the bot reads the board again:

```python
game_array = get_game_array()
```

This is important because clicking one tile can reveal several additional tiles through Minesweeper's automatic expansion.

Instead of trying to predict every resulting board change, the bot simply observes the updated game state and reasons from the new state.

The overall loop is therefore:

```text
Read Board
    ↓
Classify Tiles
    ↓
Build Grid
    ↓
Find Constraints
    ↓
Flag Mines / Reveal Safe Tiles
    ↓
Read Updated Board
    ↓
Repeat
```

---

# Project Evolution

## Version 1 — OCR-Based Solver

The original implementation used:

* PyAutoGUI screenshots
* Pillow image processing
* PyTesseract OCR
* Color checks for flags and unrevealed tiles

For each revealed tile, the program cropped the tile image and passed it through:

```python
pytesseract.image_to_string(
    block,
    config="--psm 10"
)
```

The resulting text was converted into a numerical board representation.

This approach worked conceptually, but OCR introduced unnecessary computational overhead for a game where the number colors and UI palette were already known.

---

## Version 2 — Color-Based Solver

The optimized implementation replaced OCR with direct pixel classification.

Instead of asking:

> "What number does OCR think this image contains?"

the program asks:

> "Which known game color is present at this pixel?"

This is much more appropriate for this particular environment because Google's Minesweeper interface uses a consistent visual palette.

The optimized pipeline therefore becomes:

```text
Screen
  ↓
Pixel Sampling
  ↓
RGB Classification
  ↓
Board Matrix
  ↓
Constraint Reasoning
  ↓
Mouse Actions
```

This removes the OCR processing stage entirely for normal board-state recognition.

---

# Why Color Classification?

OCR is useful when text must be interpreted from arbitrary images, but it is unnecessary when the possible outputs are known ahead of time.

In this project, the possible number values are:

```text
0, 1, 2, 3, 4, 5, 6, 7, 8
```

and the game renders those values using consistent colors.

Color classification therefore provides:

* lower processing overhead
* deterministic classification
* simpler implementation
* no OCR model dependency during the main loop
* predictable behavior for the target UI

The tradeoff is that the approach is tightly coupled to the visual appearance of the target Minesweeper implementation.

---

# Engineering Decisions

### Separate Perception From Reasoning

The computer-vision component produces a simple 2D board representation.

The reasoning system operates only on that representation.

This separation makes the solver easier to understand:

```text
Visual State → Abstract State → Decision
```

rather than mixing screen coordinates, pixel colors, and game logic throughout the solver.

### Use Relative Grid Coordinates

Rather than manually specifying every tile's screen position, the board is treated as a mathematical grid.

This makes it straightforward to convert between:

```text
(row, column)
```

and:

```text
(screen_x, screen_y)
```

### Re-Read Instead of Predicting

After taking actions, the program captures the board again rather than attempting to manually simulate every UI change.

This reduces the amount of state that the solver has to maintain internally and allows the visual system to remain the source of truth.

---

# Current Solver Strategy

The solver uses deterministic local constraints.

For each revealed number:

```text
remaining mines =
    displayed number - already flagged mines
```

Then:

```text
if remaining mines == unknown neighbors
    → all unknown neighbors are mines
```

and:

```text
if flagged mines == displayed number
    → all remaining unknown neighbors are safe
```

These rules are repeatedly applied across the board.

The solver does **not** currently implement more advanced probabilistic Minesweeper strategies such as:

* probability estimation
* global constraint solving
* subset-based constraint reduction
* minimum-risk guessing
* probabilistic first-click optimization

As a result, the implementation is focused on deterministic inference rather than attempting to solve every possible board configuration.

---

# Limitations

### Screen Layout Dependency

The current implementation uses fixed screen coordinates for the target game board.

Changing the browser window position, screen resolution, zoom level, or game layout can require recalibrating:

```python
x1, y1
x2, y2
```

### Color Dependency

The optimized solver depends on the specific colors used by the target Minesweeper interface.

A different theme or rendering configuration could require updating the RGB mappings.

### Board Size

The active configuration targets the Easy board:

```text
10 × 8
```

The code contains preliminary coordinate configurations for Medium, but the solver is not currently generalized into a dynamic board-size detection system.

### Deterministic Reasoning

The solver only makes moves when the local constraints provide a deterministic conclusion.

It does not currently make probabilistic guesses when no guaranteed safe move exists.

---

# Potential Improvements

Several extensions could make the system more general and robust:

* Automatically detect the board boundaries instead of using fixed coordinates
* Dynamically determine board dimensions
* Support Easy, Medium, and Hard boards through configuration
* Replace exact RGB matching with tolerance-based color classification
* Add probabilistic mine estimation
* Implement global constraint solving
* Add a screenshot/debug mode for inspecting misclassified tiles
* Track solver performance and decision latency
* Add configurable browser/window calibration
* Build a more generalized Minesweeper state parser that is independent of the target UI's exact colors

---

# Technologies

* **Python** — core implementation
* **PyAutoGUI** — screen interaction and mouse automation
* **Pillow** — image handling in the OCR-based implementation
* **PyTesseract** — OCR-based number recognition in the original implementation

---

# Key Takeaway

This project demonstrates a small but complete autonomous perception-and-control pipeline.

Rather than directly scripting a sequence of Minesweeper clicks, the bot:

1. **Observes** the game through the screen
2. **Converts visual information into structured state**
3. **Reasons over that state using game constraints**
4. **Executes actions through mouse input**
5. **Observes the resulting state again**
6. **Repeats until the board is solved or no deterministic action remains**

The transition from OCR to task-specific pixel classification was the main optimization in the project's development, replacing a general-purpose text-recognition technique with a lightweight vision method tailored to the known visual structure of the game.
