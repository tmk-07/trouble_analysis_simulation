"""Experiment runners for batches of Trouble simulations."""

import csv
from pathlib import Path

from .engine import simulate_game
from .strategies import strategy_furthest


def format_matchup(players):
    return " vs ".join(players)


def simulate_many_games(players, num_games=1000, max_turns=1000, strategies_by_color=None):
    """Run one matchup many times and return a summary dictionary."""
    results = {color: 0 for color in players}
    results["No winner"] = 0
    total_turns = 0
    max_turns_observed = 0

    for _ in range(num_games):
        winner, final_state = simulate_game(
            players=players,
            strategies_by_color=strategies_by_color,
            max_turns=max_turns,
            verbose=False,
        )

        if winner is None:
            results["No winner"] += 1
        else:
            results[winner] += 1

        total_turns += final_state.turn_count
        max_turns_observed = max(max_turns_observed, final_state.turn_count)

    row = {
        "matchup": format_matchup(players),
        "players": tuple(players),
        "num_games": num_games,
        "turn_limit": max_turns,
        "avg_turns": total_turns / num_games,
        "max_turns_observed": max_turns_observed,
        "wins": results,
        "win_rates": {color: results[color] / num_games * 100 for color in results},
    }

    return row


def simulate_matchups(matchups, num_games=1000, max_turns=1000, strategies_by_color=None):
    """Run multiple matchups and return one summary row per matchup."""
    summaries = []

    for players in matchups:
        summary = simulate_many_games(
            players=players,
            num_games=num_games,
            max_turns=max_turns,
            strategies_by_color=strategies_by_color,
        )
        summaries.append(summary)

    return summaries


def print_results_table(summaries):
    """Print a readable results table in the terminal."""
    all_colors = ["Blue", "Red", "Green", "Yellow", "No winner"]

    headers = [
        "Matchup",
        "Games",
        "Avg Turns",
        "Max Turns",
        *[f"{color} Win %" for color in all_colors],
    ]

    rows = []
    for summary in summaries:
        row = [
            summary["matchup"],
            str(summary["num_games"]),
            f"{summary['avg_turns']:.2f}",
            str(summary["max_turns_observed"]),
        ]

        for color in all_colors:
            if color in summary["win_rates"]:
                row.append(f"{summary['win_rates'][color]:.2f}")
            else:
                row.append("-")

        rows.append(row)

    widths = [len(header) for header in headers]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(cell))

    def make_line(values):
        return " | ".join(str(value).ljust(widths[i]) for i, value in enumerate(values))

    print("\nSimulation Results")
    print("=" * (sum(widths) + 3 * (len(widths) - 1)))
    print(make_line(headers))
    print("-" * (sum(widths) + 3 * (len(widths) - 1)))
    for row in rows:
        print(make_line(row))


def save_results_csv(summaries, filename="results.csv"):
    """
    Save a clean CSV for spreadsheet analysis.

    The CSV intentionally keeps only:
    - matchup, so each row is identifiable
    - number of games
    - average turns
    - max turns observed
    - win rate for each color

    Raw win counts, turn limit, and no-winner rate are left out to keep the
    spreadsheet compact.
    """
    colors = ["Blue", "Red", "Green", "Yellow"]
    path = Path(filename)

    fieldnames = [
        "matchup",
        "num_games",
        "avg_turns",
        "max_turns_observed",
        *[f"{color}_win_rate" for color in colors],
    ]

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for summary in summaries:
            row = {
                "matchup": summary["matchup"],
                "num_games": summary["num_games"],
                "avg_turns": f"{summary['avg_turns']:.4f}",
                "max_turns_observed": summary["max_turns_observed"],
            }

            for color in colors:
                row[f"{color}_win_rate"] = f"{summary['win_rates'].get(color, 0):.4f}"

            writer.writerow(row)

    return path
