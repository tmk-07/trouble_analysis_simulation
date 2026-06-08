from trouble_sim.rl_training import train_rl_agent


if __name__ == "__main__":
    train_rl_agent(
        batches=16251,
        games_per_batch=1000,
        learning_rate=0.01,
        opponent_strategy_name="double_capture_furthest",
        max_turns=1000,
        temperature=0.25,
        seed=None,
        save_path="results/rl/rl_weights_v2_danger_count_no_home.json",
        history_csv_path="results/rl/rl_training_history_v2_danger_count_no_home.csv",
        reset_history=False,
        load_existing_weights=True,
    )