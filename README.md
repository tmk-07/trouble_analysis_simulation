# Trouble Strategy Simulator

A Python-based simulation and strategy analysis project for the board game **Trouble**. This project models game rules, runs large-scale simulations, compares different strategies, visualizes matches, and includes a feature-based reinforcement learning bot trained against strong heuristic opponents.

## Project Rundown

For a more detailed explanation of how the project developed, including design decisions, training experiments, findings, and conclusions, see the full project writeup:

[View Project Rundown PDF](docs/project-rundown.pdf)

## Features

### Core Game Engine

* Simulates Trouble games with 2, 3, or 4 players
* Tracks board position, piece progress, home pieces, completed pieces, captures, and turn order
* Supports multiple player colors: Blue, Red, Green, and Yellow
* Handles legal move generation for each dice roll
* Supports captures and sends captured pieces back home
* Supports double spots that grant extra turns
* Detects winners automatically when all pieces are finished
* Allows customizable maximum turn limits to prevent endless simulations

### Strategy System

The project includes several built-in strategies that can be assigned to different players:

* `random` — chooses randomly from all legal moves
* `furthest` — moves the piece with the most progress
* `double_capture_furthest` — prioritizes landing on double spots, then captures, then progress
* `capture_double_furthest` — prioritizes captures, then double spots, then progress
* `conservative` — uses safer move choices to reduce capture risk
* `rl_bot` — uses learned feature weights from reinforcement learning training

This strategy system makes it easy to test different decision-making styles against one another.

### Monte Carlo Simulation

* Runs large batches of simulated games
* Calculates win rates across thousands of trials
* Measures average game length
* Compares performance across player counts
* Supports repeated simulations for more reliable results
* Outputs results to CSV files for analysis

### Tournament Evaluation

* Runs strategy tournaments across different player counts
* Supports 2-player, 3-player, and 4-player matchups
* Compares strategies across many game combinations
* Produces leaderboard-style results
* Generates matchup and profile summaries
* Supports head-to-head testing for 2-player strategy comparisons

### Reinforcement Learning Bot

The project includes a custom reinforcement learning agent that learns how to select moves based on game-state features.

The RL bot uses a feature-based policy rather than a neural network. Each legal move is converted into a set of numeric features, and the bot learns weights for those features over many simulated games.

Features used by the RL bot include:

* finishing a piece
* capturing an opponent
* landing on a double spot
* piece progress
* danger of being captured
* danger reduction
* progress of captured opponent pieces

During training, the bot explores moves using a softmax policy. During testing, the bot runs in evaluation mode and chooses the highest-scoring move based on its learned weights.

### RL Training System

* Trains the RL bot against heuristic opponents
* Supports batch-based weight updates
* Tracks reward, win rate, captures, pieces finished, and average turns
* Saves learned weights to JSON files
* Saves training history to CSV files
* Supports continued training from previous weights
* Supports testing with frozen weights so the bot does not keep learning during evaluation

### Bot Testing and Evaluation

* Tests the trained bot against strong heuristic opponents
* Runs the bot in `training=False` mode during evaluation
* Supports balanced testing across turn positions
* Measures win rate by turn position
* Compares bot results against the 25% baseline for 4-player games
* Outputs evaluation results to CSV

### Data and Results

The project can generate:

* tournament leaderboards
* head-to-head matchup results
* RL training history
* bot evaluation summaries
* win-rate data
* average turn counts
* learned feature-weight changes

### Visualization

The project includes a Pygame-based replay viewer for watching simulated games visually.

The viewer displays:

* board layout
* player pieces
* home and finished pieces
* dice rolls
* captures
* current player
* turn-by-turn game progression

This was useful for debugging the engine, checking strategy behavior, and making the project easier to demonstrate.

## Technologies Used

* Python
* Object-oriented programming
* Monte Carlo simulation
* CSV data output
* Matplotlib plotting
* Pygame visualization
* Feature-based reinforcement learning
* Strategy evaluation and tournament analysis
