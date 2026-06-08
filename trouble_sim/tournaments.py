"""Strategy tournament tools.

This module runs round-robin style tournaments between strategies.

It supports:
- 2-player tournaments
- 3-player tournaments
- 4-player tournaments

Each tournament mixes color order / first mover by running all ordered color
permutations, but profile results are aggregated by unordered strategy
combinations.

Example:
    random vs furthest vs conservative
    furthest vs random vs conservative
    conservative vs furthest vs random

all combine into one row:
    conservative vs furthest vs random
"""

from collections import Counter
from itertools import permutations, product, combinations_with_replacement
import csv
from pathlib import Path

from .constants import COLORS
from .engine import simulate_game


DEFAULT_TOURNAMENT_STRATEGIES = [
    "random",
    "furthest",
    "double_capture_furthest",
    "capture_double_furthest",
    "conservative",
]


def get_color_orders(player_count):
    """
    Return all ordered color selections for the player count.

    The order matters because the first color in the list goes first.

    Example for 2 players:
        ("Blue", "Red")
        ("Red", "Blue")
        ("Blue", "Green")
        ("Green", "Blue")
    """
    return list(permutations(COLORS, player_count))


def make_empty_strategy_record():
    return {
        "appearances": 0,
        "wins": 0,
        "total_turns": 0,
        "max_turns_observed": 0,
        "win_rate": 0.0,
        "avg_turns": 0.0,
    }


def canonical_strategy_profile(strategy_profile):
    """
    Convert an ordered strategy profile into an unordered canonical key.

    Examples:
        ("random", "furthest", "conservative")
        ("furthest", "random", "conservative")

    both become:
        ("conservative", "furthest", "random")

    Duplicate strategies are preserved:
        ("random", "random", "furthest")
    becomes:
        ("furthest", "random", "random")
    """
    return tuple(sorted(strategy_profile))


def summarize_leaderboard(strategy_records):
    """
    Convert raw strategy records into win rates and turn statistics.

    appearances means total number of times the strategy appeared as a player
    across all games.
    """
    summary = {}

    for strategy_name, record in strategy_records.items():
        appearances = record["appearances"]
        wins = record["wins"]
        total_turns = record["total_turns"]

        win_rate = wins / appearances if appearances > 0 else 0
        avg_turns = total_turns / appearances if appearances > 0 else 0

        summary[strategy_name] = {
            "appearances": appearances,
            "wins": wins,
            "win_rate": win_rate,
            "avg_turns": avg_turns,
            "max_turns_observed": record["max_turns_observed"],
        }

    return summary


def build_profile_results(profile_results_map, strategy_names):
    """
    Convert aggregated profile records into a clean list of profile summaries.

    Each row represents one unordered strategy combination.
    """
    profile_results = []

    for canonical_profile, profile_record in profile_results_map.items():
        num_games = profile_record["num_games"]

        win_rates = {
            strategy: profile_record["wins"][strategy] / num_games if num_games else 0
            for strategy in strategy_names
        }

        profile_results.append({
            "strategy_profile": profile_record["strategy_profile"],
            "player_count": profile_record["player_count"],
            "num_games": num_games,
            "avg_turns": (
                profile_record["total_turns"] / num_games if num_games else 0
            ),
            "max_turns_observed": profile_record["max_turns_observed"],
            "first_player_win_rate": (
                profile_record["first_player_wins"] / num_games if num_games else 0
            ),
            "no_winner_rate": (
                profile_record["no_winner_count"] / num_games if num_games else 0
            ),
            "wins": dict(profile_record["wins"]),
            "win_rates": win_rates,
        })

    profile_results.sort(key=lambda row: row["strategy_profile"])
    return profile_results


def run_strategy_tournament(
    player_count,
    strategy_names=None,
    games_per_setting=100,
    max_turns=1000,
):
    """
    Run one tournament for a fixed player count.

    player_count:
        2, 3, or 4

    strategy_names:
        list of strategy names already registered in strategies.py

    games_per_setting:
        number of games to simulate for each ordered strategy profile and
        ordered color setup.

    Returns a dictionary with:
        - player_count
        - strategy_names
        - games_per_setting
        - total_games
        - leaderboard
        - profile_results
        - first_player_win_rate
    """

    if strategy_names is None:
        strategy_names = DEFAULT_TOURNAMENT_STRATEGIES

    if player_count not in (2, 3, 4):
        raise ValueError("player_count must be 2, 3, or 4.")

    color_orders = get_color_orders(player_count)

    # A strategy profile is a strategy assigned to each turn-order seat.
    # Example for 3 players:
    #     ("random", "furthest", "conservative")
    strategy_profiles = list(product(strategy_names, repeat=player_count))

    strategy_records = {
        strategy: make_empty_strategy_record()
        for strategy in strategy_names
    }

    # Aggregated profile rows.
    # Ordered profiles are simulated, but results are merged by sorted profile.
    profile_results_map = {}

    total_games = 0
    total_turns = 0
    max_turns_observed = 0

    first_player_wins = 0
    no_winner_count = 0

    for strategy_profile in strategy_profiles:
        canonical_profile = canonical_strategy_profile(strategy_profile)

        if canonical_profile not in profile_results_map:
            profile_results_map[canonical_profile] = {
                "strategy_profile": " vs ".join(canonical_profile),
                "player_count": player_count,
                "num_games": 0,
                "total_turns": 0,
                "max_turns_observed": 0,
                "first_player_wins": 0,
                "no_winner_count": 0,
                "wins": Counter(),
            }

        profile_record = profile_results_map[canonical_profile]

        for color_order in color_orders:
            players = list(color_order)

            strategies_by_color = {
                color: strategy_profile[index]
                for index, color in enumerate(players)
            }

            first_player = players[0]

            for _ in range(games_per_setting):
                winner, final_state = simulate_game(
                    players=players,
                    strategies_by_color=strategies_by_color,
                    max_turns=max_turns,
                    verbose=False,
                )

                total_games += 1
                total_turns += final_state.turn_count
                max_turns_observed = max(
                    max_turns_observed,
                    final_state.turn_count,
                )

                profile_record["num_games"] += 1
                profile_record["total_turns"] += final_state.turn_count
                profile_record["max_turns_observed"] = max(
                    profile_record["max_turns_observed"],
                    final_state.turn_count,
                )

                # Count one appearance per strategy-controlled player.
                for color in players:
                    strategy = strategies_by_color[color]

                    strategy_records[strategy]["appearances"] += 1
                    strategy_records[strategy]["total_turns"] += final_state.turn_count
                    strategy_records[strategy]["max_turns_observed"] = max(
                        strategy_records[strategy]["max_turns_observed"],
                        final_state.turn_count,
                    )

                if winner is None:
                    no_winner_count += 1
                    profile_record["no_winner_count"] += 1
                    continue

                winning_strategy = strategies_by_color[winner]

                strategy_records[winning_strategy]["wins"] += 1
                profile_record["wins"][winning_strategy] += 1

                if winner == first_player:
                    first_player_wins += 1
                    profile_record["first_player_wins"] += 1

    leaderboard = summarize_leaderboard(strategy_records)
    profile_results = build_profile_results(profile_results_map, strategy_names)

    tournament_summary = {
        "player_count": player_count,
        "strategy_names": strategy_names,
        "games_per_setting": games_per_setting,
        "color_orders_tested": len(color_orders),
        "strategy_profiles_tested": len(strategy_profiles),
        "distinct_strategy_profiles": len(profile_results),
        "total_games": total_games,
        "avg_turns": total_turns / total_games if total_games else 0,
        "max_turns_observed": max_turns_observed,
        "first_player_win_rate": first_player_wins / total_games if total_games else 0,
        "no_winner_rate": no_winner_count / total_games if total_games else 0,
        "leaderboard": leaderboard,
        "profile_results": profile_results,
    }

    return tournament_summary


def run_two_player_head_to_head(
    strategy_names=None,
    games_per_setting=100,
    max_turns=1000,
):
    """
    Run a clean 2-player head-to-head tournament.

    Returns one row per unique strategy pair:
        random vs furthest
        random vs conservative
        furthest vs conservative
        etc.

    It mixes:
    - both seat orders, A vs B and B vs A, unless A == B
    - all 2-player color orders

    So first mover gets mixed fairly.
    """

    if strategy_names is None:
        strategy_names = DEFAULT_TOURNAMENT_STRATEGIES

    color_orders = get_color_orders(2)
    pair_results = []

    for strategy_a, strategy_b in combinations_with_replacement(strategy_names, 2):
        # If both strategies are the same, no need to run both seat orders.
        if strategy_a == strategy_b:
            seat_orders = [(strategy_a, strategy_b)]
        else:
            seat_orders = [
                (strategy_a, strategy_b),
                (strategy_b, strategy_a),
            ]

        wins = Counter()
        total_games = 0
        total_turns = 0
        max_turns_observed = 0
        first_strategy_wins = 0
        no_winner_count = 0

        for strategy_profile in seat_orders:
            for color_order in color_orders:
                players = list(color_order)

                strategies_by_color = {
                    players[0]: strategy_profile[0],
                    players[1]: strategy_profile[1],
                }

                first_strategy = strategy_profile[0]

                for _ in range(games_per_setting):
                    winner, final_state = simulate_game(
                        players=players,
                        strategies_by_color=strategies_by_color,
                        max_turns=max_turns,
                        verbose=False,
                    )

                    total_games += 1
                    total_turns += final_state.turn_count
                    max_turns_observed = max(
                        max_turns_observed,
                        final_state.turn_count,
                    )

                    if winner is None:
                        no_winner_count += 1
                        continue

                    winning_strategy = strategies_by_color[winner]
                    wins[winning_strategy] += 1

                    if winning_strategy == first_strategy:
                        first_strategy_wins += 1

        row = {
            "strategy_a": strategy_a,
            "strategy_b": strategy_b,
            "num_games": total_games,
            "avg_turns": total_turns / total_games if total_games else 0,
            "max_turns_observed": max_turns_observed,
            "first_strategy_win_rate": (
                first_strategy_wins / total_games if total_games else 0
            ),
            "no_winner_rate": no_winner_count / total_games if total_games else 0,
            "strategy_a_wins": wins[strategy_a],
            "strategy_b_wins": wins[strategy_b],
            "strategy_a_win_rate": wins[strategy_a] / total_games if total_games else 0,
            "strategy_b_win_rate": wins[strategy_b] / total_games if total_games else 0,
        }

        pair_results.append(row)

    return pair_results


def run_all_tournaments(
    strategy_names=None,
    games_per_setting=100,
    max_turns=1000,
):
    """
    Run 2-player, 3-player, and 4-player strategy tournaments.

    Returns:
        {
            "two_player": {...},
            "three_player": {...},
            "four_player": {...}
        }
    """

    two_player = run_strategy_tournament(
        player_count=2,
        strategy_names=strategy_names,
        games_per_setting=games_per_setting,
        max_turns=max_turns,
    )

    # Add a clean head-to-head breakdown for 2-player only.
    two_player["head_to_head_results"] = run_two_player_head_to_head(
        strategy_names=strategy_names,
        games_per_setting=games_per_setting,
        max_turns=max_turns,
    )

    return {
        "two_player": two_player,
        "three_player": run_strategy_tournament(
            player_count=3,
            strategy_names=strategy_names,
            games_per_setting=games_per_setting,
            max_turns=max_turns,
        ),
        "four_player": run_strategy_tournament(
            player_count=4,
            strategy_names=strategy_names,
            games_per_setting=games_per_setting,
            max_turns=max_turns,
        ),
    }


def print_tournament_leaderboard(tournament_summary):
    """
    Print a readable leaderboard for one tournament.
    """
    player_count = tournament_summary["player_count"]

    print(f"\n{player_count}-Player Strategy Tournament")
    print("-" * 40)
    print(f"Total games: {tournament_summary['total_games']}")
    print(f"Ordered profiles tested: {tournament_summary['strategy_profiles_tested']}")
    print(f"Distinct profiles saved: {tournament_summary['distinct_strategy_profiles']}")
    print(f"Avg turns: {tournament_summary['avg_turns']:.2f}")
    print(f"Max turns observed: {tournament_summary['max_turns_observed']}")
    print(f"First-player win rate: {tournament_summary['first_player_win_rate'] * 100:.2f}%")
    print(f"No-winner rate: {tournament_summary['no_winner_rate'] * 100:.2f}%")

    print("\nLeaderboard")
    print("-" * 40)

    leaderboard = tournament_summary["leaderboard"]

    sorted_rows = sorted(
        leaderboard.items(),
        key=lambda item: item[1]["win_rate"],
        reverse=True,
    )

    for strategy, record in sorted_rows:
        print(
            f"{strategy:28s} "
            f"wins={record['wins']:8d} "
            f"appearances={record['appearances']:8d} "
            f"win_rate={record['win_rate'] * 100:6.2f}% "
            f"avg_turns={record['avg_turns']:7.2f}"
        )


def save_tournament_leaderboard_csv(tournament_summary, filename):
    """
    Save the tournament leaderboard to CSV.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "player_count",
        "strategy",
        "appearances",
        "wins",
        "win_rate",
        "total_games",
        "avg_turns",
        "max_turns_observed",
        "first_player_win_rate",
        "no_winner_rate",
    ]

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for strategy, record in tournament_summary["leaderboard"].items():
            writer.writerow({
                "player_count": tournament_summary["player_count"],
                "strategy": strategy,
                "appearances": record["appearances"],
                "wins": record["wins"],
                "win_rate": record["win_rate"],
                "total_games": tournament_summary["total_games"],
                "avg_turns": record["avg_turns"],
                "max_turns_observed": record["max_turns_observed"],
                "first_player_win_rate": tournament_summary["first_player_win_rate"],
                "no_winner_rate": tournament_summary["no_winner_rate"],
            })

    return path


def save_tournament_profiles_csv(tournament_summary, filename):
    """
    Save strategy-profile-level results to CSV.

    Each row is one DISTINCT unordered strategy combination after mixing all
    seat orders, first movers, and color orders.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    strategy_names = tournament_summary["strategy_names"]

    fieldnames = [
        "player_count",
        "strategy_profile",
        "num_games",
        "avg_turns",
        "max_turns_observed",
        "first_player_win_rate",
        "no_winner_rate",
        *[f"{strategy}_win_rate" for strategy in strategy_names],
    ]

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for profile in tournament_summary["profile_results"]:
            row = {
                "player_count": profile["player_count"],
                "strategy_profile": profile["strategy_profile"],
                "num_games": profile["num_games"],
                "avg_turns": profile["avg_turns"],
                "max_turns_observed": profile["max_turns_observed"],
                "first_player_win_rate": profile["first_player_win_rate"],
                "no_winner_rate": profile["no_winner_rate"],
            }

            for strategy in strategy_names:
                row[f"{strategy}_win_rate"] = profile["win_rates"].get(strategy, 0)

            writer.writerow(row)

    return path


def save_two_player_head_to_head_csv(pair_results, filename):
    """
    Save 2-player head-to-head results to CSV.

    Keeps only win rates, not raw win counts.
    Also removes no-winner rate.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "strategy_a",
        "strategy_b",
        "num_games",
        "avg_turns",
        "max_turns_observed",
        "first_strategy_win_rate",
        "strategy_a_win_rate",
        "strategy_b_win_rate",
    ]

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in pair_results:
            writer.writerow({
                "strategy_a": row["strategy_a"],
                "strategy_b": row["strategy_b"],
                "num_games": row["num_games"],
                "avg_turns": row["avg_turns"],
                "max_turns_observed": row["max_turns_observed"],
                "first_strategy_win_rate": row["first_strategy_win_rate"],
                "strategy_a_win_rate": row["strategy_a_win_rate"],
                "strategy_b_win_rate": row["strategy_b_win_rate"],
            })

    return path
    """
    Save 2-player head-to-head results to CSV.
    """
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "strategy_a",
        "strategy_b",
        "num_games",
        "avg_turns",
        "max_turns_observed",
        "first_strategy_win_rate",
        "no_winner_rate",
        "strategy_a_wins",
        "strategy_b_wins",
        "strategy_a_win_rate",
        "strategy_b_win_rate",
    ]

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for row in pair_results:
            writer.writerow(row)

    return path