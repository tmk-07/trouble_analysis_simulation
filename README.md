# Trouble Strategy Simulator

A Python simulation engine for studying turn order, board position, and move-selection strategy in the board game **Trouble**.

The current version models a simplified Trouble-style game with fixed color start positions, dice rolls, captures, extra-turn spaces, finishing after one full lap, and interchangeable strategy functions.

## Project Goals

This project investigates questions like:

- Does the first player have a measurable advantage?
- Do certain starting positions perform better than others?
- How much does move strategy affect long-term win percentage?
- Can stronger strategies be discovered through simulation, Monte Carlo search, or self-play?

## Current Features

- Fixed color starting positions:
  - Blue: 0
  - Red: 7
  - Green: 14
  - Yellow: 21
- 28-space circular board
- 4 pieces per player
- No 6 required to leave home
- Captures send opponent pieces back home
- No stacking on your own pieces
- Extra turn for landing on a double spot
- Simplified finish rule: a piece is done after one full lap
- Strategy system separated from the game engine
- Batch experiment runner for multiple matchups
- Terminal table output
- Optional CSV export

## Project Structure

```text
trouble_strategy_simulator/
│
├── main.py
├── README.md
├── requirements.txt
├── .gitignore
│
└── trouble_sim/
    ├── __init__.py
    ├── constants.py
    ├── game_state.py
    ├── engine.py
    ├── strategies.py
    ├── ascii_board.py
    └── experiments.py
```

## How to Run

From the project folder:

```bash
python main.py
```

This runs several matchups and prints a results table.

Example matchups are defined in `main.py`:

```python
MATCHUPS = [
    ["Blue", "Red"],
    ["Blue", "Green"],
    ["Blue", "Yellow"],
    ["Green", "Blue"],
    ["Yellow", "Blue"],
    ["Blue", "Red", "Green"],
    ["Blue", "Red", "Green", "Yellow"],
]
```

## Example Output

```text
Simulation Results
===============================================================================================
Matchup                       | Games | Avg Turns | Max Turns | Blue Win % | Red Win % | Green Win % | Yellow Win % | No winner Win %
------------------------------------------------------------------------------------------------
Blue vs Red                   | 10000 | 83.42     | 219       | 52.31      | 47.69     | -           | -            | 0.00
Blue vs Green                 | 10000 | 84.05     | 236       | 51.87      | -         | 48.13       | -            | 0.00
Blue vs Red vs Green          | 10000 | 102.27    | 301       | 34.91      | 32.40     | 32.69       | -            | 0.00
```

Exact numbers will vary because dice rolls are random.

## Strategies

Strategies live in:

```text
trouble_sim/strategies.py
```

Current strategies:

```python
"random"
"furthest"
```

The default/current strategy is **furthest**, meaning the player always moves the legal piece with the most progress.

## Changing Strategies

In `main.py`, you can assign strategies by color:

```python
strategies_by_color={
    "Blue": "furthest",
    "Red": "furthest",
    "Green": "furthest",
    "Yellow": "furthest",
}
```

Later, you can add new strategies such as:

- capture first
- finish first
- double-spot priority
- scored heuristic
- Monte Carlo rollout strategy
- reinforcement learning / self-play strategy

## Future Work

Possible next steps:

- Add real Trouble finish lanes
- Require exact rolls to finish
- Add more strategy agents
- Add Monte Carlo move selection
- Tune heuristic strategy weights through self-play
- Export full simulation logs
- Create charts from CSV results
- Mathematically model matchups as Markov chains

## Pygame Single-Game Replay Viewer

This project includes a simple Pygame replay viewer for watching one simulated game turn by turn.

Install requirements:

```bash
pip install -r requirements.txt
```

Run the visual replay:

```bash
python run_pygame_match.py
```

Controls:

- `SPACE` or `RIGHT`: next move
- `LEFT`: previous move
- `A`: autoplay
- `R`: simulate a new game with the same matchup/settings
- `ESC`: quit

You can edit `run_pygame_match.py` to change the matchup or strategies:

```python
watch_match(
    players=["Blue", "Green"],
    strategies_by_color={
        "Blue": "furthest",
        "Green": "random",
    },
    max_turns=1000,
)
```

The replay viewer is intentionally separate from the game engine. The simulator first records replay frames, then Pygame reads those frames so the visualization does not affect game logic.
