"""Evaluate trained RL bot with equal turn-order distribution."""

import csv
import random
from collections import Counter
from pathlib import Path

from trouble_sim.engine import simulate_game
from trouble_sim.rl_agent import RLAgent


BOT_COLOR = "Blue"
ALL_COLORS = ["Blue", "Red", "Green", "Yellow"]

NUM_GAMES = 10000
MAX_TURNS = 1000

WEIGHTS_PATH = "results/rl/rl_weights_v2_danger_count_no_home.json"
OUTPUT_CSV = "results/rl/eval_v2_equal_turn_order.csv"


def make_players_with_bot_position(bot_position):
    """
    Create a 4-player order where the RL bot appears in a specific turn slot.

    bot_position:
        0 = first
        1 = second
        2 = third
        3 = fourth
    """
    opponents = [color for color in ALL_COLORS if color != BOT_COLOR]
    random.shuffle(opponents)

    players = opponents[:]
    players.insert(bot_position, BOT_COLOR)

    return players


def evaluate_bot():
    if NUM_GAMES % 4 != 0:
        raise ValueError("NUM_GAMES should be divisible by 4 for equal turn-order testing.")

    games_per_position = NUM_GAMES // 4

    trained_bot = RLAgent(training=False)
    trained_bot.load_weights(WEIGHTS_PATH)

    overall_wins = Counter()
    position_rows = []

    total_turns = 0
    bot_total_wins = 0

    for bot_position in range(4):
        position_wins = Counter()
        position_turns = 0
        bot_wins_this_position = 0

        for _ in range(games_per_position):
            players = make_players_with_bot_position(bot_position)

            strategies_by_color = {
                BOT_COLOR: trained_bot,
                "Red": "double_capture_furthest",
                "Green": "double_capture_furthest",
                "Yellow": "double_capture_furthest",
            }

            winner, final_state = simulate_game(
                players=players,
                strategies_by_color=strategies_by_color,
                max_turns=MAX_TURNS,
                verbose=False,
            )

            overall_wins[winner] += 1
            position_wins[winner] += 1

            total_turns += final_state.turn_count
            position_turns += final_state.turn_count

            if winner == BOT_COLOR:
                bot_total_wins += 1
                bot_wins_this_position += 1

        row = {
            "bot_turn_position": bot_position + 1,
            "num_games": games_per_position,
            "bot_wins": bot_wins_this_position,
            "bot_win_rate": bot_wins_this_position / games_per_position,
            "avg_turns": position_turns / games_per_position,
            "red_win_rate": position_wins["Red"] / games_per_position,
            "green_win_rate": position_wins["Green"] / games_per_position,
            "yellow_win_rate": position_wins["Yellow"] / games_per_position,
            "no_winner_rate": position_wins[None] / games_per_position,
        }

        position_rows.append(row)

    overall_bot_win_rate = bot_total_wins / NUM_GAMES
    avg_turns = total_turns / NUM_GAMES

    print("\nTrained RL Bot Evaluation")
    print("-" * 45)
    print(f"Games: {NUM_GAMES}")
    print(f"Weights: {WEIGHTS_PATH}")
    print(f"Bot color: {BOT_COLOR}")
    print(f"Bot mode: training=False")
    print(f"Opponents: double_capture_furthest")
    print(f"Overall bot win rate: {overall_bot_win_rate * 100:.2f}%")
    print(f"Average turns: {avg_turns:.2f}")

    print("\nBy turn position")
    print("-" * 45)
    for row in position_rows:
        print(
            f"Position {row['bot_turn_position']}: "
            f"{row['bot_win_rate'] * 100:.2f}% win rate "
            f"({row['bot_wins']}/{row['num_games']})"
        )

    save_eval_csv(position_rows, overall_bot_win_rate, avg_turns)


def save_eval_csv(position_rows, overall_bot_win_rate, overall_avg_turns):
    path = Path(OUTPUT_CSV)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "bot_turn_position",
        "num_games",
        "bot_wins",
        "bot_win_rate",
        "avg_turns",
        "red_win_rate",
        "green_win_rate",
        "yellow_win_rate",
        "no_winner_rate",
        "overall_bot_win_rate",
        "overall_avg_turns",
    ]

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in position_rows:
            row = row.copy()
            row["overall_bot_win_rate"] = overall_bot_win_rate
            row["overall_avg_turns"] = overall_avg_turns
            writer.writerow(row)

    print(f"\nSaved evaluation CSV to {OUTPUT_CSV}")


if __name__ == "__main__":
    evaluate_bot()