"""Run Trouble simulation experiments with trained RL bot."""

from trouble_sim.experiments import (
    print_results_table,
    save_results_csv,
    simulate_matchups,
)
from trouble_sim.rl_agent import RLAgent


MATCHUPS = [
    ["Blue", "Red"],
    ["Blue", "Green"],
    ["Blue", "Yellow"],
    ["Blue", "Red", "Green"],
    ["Blue", "Red", "Yellow"],
    ["Blue", "Green", "Yellow"],
    ["Blue", "Red", "Green", "Yellow"],
]


if __name__ == "__main__":
    # Load trained RL bot.
    trained_bot = RLAgent(training=False)
    trained_bot.load_weights("results/rl/rl_weights_v2_danger_count_no_home.json")

    summaries = simulate_matchups(
        matchups=MATCHUPS,
        num_games=1000,
        max_turns=1000,
        strategies_by_color={
            # Blue is the trained RL bot.
            "Blue": trained_bot,

            # Everyone else uses the strongest heuristic so far.
            "Red": "double_capture_furthest",
            "Green": "double_capture_furthest",
            "Yellow": "double_capture_furthest",
        },
    )

    print_results_table(summaries)
    save_results_csv(summaries, "results_rl_vs_double_capture.csv")
    print("\nSaved CSV results to results_rl_vs_double_capture.csv")