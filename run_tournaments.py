from trouble_sim.tournaments import (
    DEFAULT_TOURNAMENT_STRATEGIES,
    run_strategy_tournament,
    run_two_player_head_to_head,
    print_tournament_leaderboard,
    save_tournament_leaderboard_csv,
    save_tournament_profiles_csv,
    save_two_player_head_to_head_csv,
)

import time


# -----------------------------
# Settings
# -----------------------------

# Choose one:
# 2 = two-player tournament
# 3 = three-player tournament
# 4 = four-player tournament
PLAYER_COUNT = 4

GAMES_PER_SETTING = 100
MAX_TURNS = 1000

STRATEGIES = DEFAULT_TOURNAMENT_STRATEGIES


# -----------------------------
# Run one tournament
# -----------------------------

if __name__ == "__main__":
    start = time.time()

    print(f"\nRunning {PLAYER_COUNT}-player tournament...")
    print(f"Strategies: {STRATEGIES}")
    print(f"Games per setting: {GAMES_PER_SETTING}")
    print(f"Max turns per game: {MAX_TURNS}")

    summary = run_strategy_tournament(
        player_count=PLAYER_COUNT,
        strategy_names=STRATEGIES,
        games_per_setting=GAMES_PER_SETTING,
        max_turns=MAX_TURNS,
    )

    print_tournament_leaderboard(summary)

    save_tournament_leaderboard_csv(
        summary,
        f"results/tournaments/{PLAYER_COUNT}_player_leaderboard.csv",
    )

    save_tournament_profiles_csv(
        summary,
        f"results/tournaments/{PLAYER_COUNT}_player_profiles.csv",
    )

    # Extra detailed head-to-head file only makes sense for 2-player.
    if PLAYER_COUNT == 2:
        print("\nRunning 2-player head-to-head breakdown...")

        head_to_head_results = run_two_player_head_to_head(
            strategy_names=STRATEGIES,
            games_per_setting=GAMES_PER_SETTING,
            max_turns=MAX_TURNS,
        )

        save_two_player_head_to_head_csv(
            head_to_head_results,
            "results/tournaments/2_player_head_to_head.csv",
        )

    end = time.time()
    print(f"\nRuntime: {end - start:.2f} seconds")