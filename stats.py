"""Calculate RL bot win rate over the most recent training games."""

import csv
from pathlib import Path


HISTORY_CSV = Path("results/rl/rl_training_history_v2_danger_count_no_home.csv")

LAST_N_GAMES = 200

# Set this to whatever you used in train_rl_bot.py.
# Example: if every batch trained 1000 games, use 1000.
GAMES_PER_BATCH = 1000


def get_win_rate_column(fieldnames):
    """
    Find the win-rate column in the CSV.
    """
    possible_names = [
        "win_rate",
        "avg_win_rate",
        "rl_win_rate",
        "batch_win_rate",
    ]

    for name in possible_names:
        if name in fieldnames:
            return name

    raise ValueError(
        f"Could not find a win-rate column. CSV columns are: {fieldnames}"
    )


def calculate_recent_win_rate():
    if not HISTORY_CSV.exists():
        raise FileNotFoundError(f"Could not find {HISTORY_CSV}")

    with HISTORY_CSV.open("r", newline="") as file:
        reader = csv.DictReader(file)
        rows = list(reader)

    if not rows:
        raise ValueError("Training history CSV is empty.")

    win_rate_column = get_win_rate_column(reader.fieldnames)

    remaining_games = LAST_N_GAMES
    weighted_wins = 0
    counted_games = 0

    # Work backwards from most recent batch.
    for row in reversed(rows):
        batch_win_rate = float(row[win_rate_column])

        # Use column from CSV if it exists, otherwise use default.
        if "games_per_batch" in row and row["games_per_batch"]:
            batch_games = int(row["games_per_batch"])
        elif "num_games" in row and row["num_games"]:
            batch_games = int(row["num_games"])
        else:
            batch_games = GAMES_PER_BATCH

        games_to_use = min(batch_games, remaining_games)

        weighted_wins += batch_win_rate * games_to_use
        counted_games += games_to_use
        remaining_games -= games_to_use

        if remaining_games == 0:
            break

    recent_win_rate = weighted_wins / counted_games

    print("\nRecent RL Training Win Rate")
    print("-" * 40)
    print(f"CSV: {HISTORY_CSV}")
    print(f"Games counted: {counted_games}")
    print(f"Average win rate over last {counted_games} games: {recent_win_rate * 100:.2f}%")


if __name__ == "__main__":
    calculate_recent_win_rate()