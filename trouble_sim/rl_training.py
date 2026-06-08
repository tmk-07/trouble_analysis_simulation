"""Training loop for the RL bot."""

import random

from pathlib import Path
from .constants import COLORS
from .game_state import GameState
from .engine import (
    roll_dice,
    get_legal_moves,
    apply_move,
    check_winner,
    move_lands_on_double_spot,
)
from .strategies import STRATEGIES
from .rl_agent import RLAgent

def append_training_history_csv(history_rows, filename):
    """
    Append RL training progress to a lifetime CSV.

    This does not overwrite previous runs.
    """
    import csv
    from pathlib import Path

    if not history_rows:
        return None

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    file_exists = path.exists()

    fieldnames = list(history_rows[0].keys())

    with path.open("a", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerows(history_rows)

    return path

def get_last_lifetime_batch(history_csv_path):
    """
    Read the existing history CSV and return the last lifetime batch number.

    If no history file exists yet, return 0.
    """
    import csv
    from pathlib import Path

    path = Path(history_csv_path)

    if not path.exists():
        return 0

    last_batch = 0

    with path.open("r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            if "lifetime_batch" in row and row["lifetime_batch"]:
                last_batch = max(last_batch, int(row["lifetime_batch"]))

    return last_batch


def make_run_id():
    """
    Create a readable ID for one training run.
    """
    from datetime import datetime

    return datetime.now().strftime("%Y%m%d_%H%M%S")



def simulate_training_game(
    agent,
    opponent_strategy_name="double_capture_furthest",
    max_turns=1000,
):
    """
    Simulate one 4-player training game.

    One randomly chosen color uses the RL agent.
    The other three colors use the opponent strategy.
    Turn order is randomized by shuffling the players list.

    Fine-tuning reward formula:
    - Winning/losing matters much more than side objectives.
    - Finishing pieces still matters.
    - Captures are rewarded only lightly.
    """

    players = list(COLORS)
    random.shuffle(players)

    rl_color = random.choice(players)
    opponent_strategy = STRATEGIES[opponent_strategy_name]

    strategies_by_color = {
        color: opponent_strategy
        for color in players
    }
    strategies_by_color[rl_color] = agent

    state = GameState(players)

    agent.start_episode()

    rl_captures = 0
    rl_capture_progress_total = 0.0

    while state.winner is None and state.turn_count < max_turns:
        color = state.current_player()
        roll = roll_dice()

        legal_moves = get_legal_moves(state, color, roll)
        strategy = strategies_by_color[color]
        move = strategy(state, color, roll, legal_moves)

        # Track RL captures before apply_move resets captured piece progress.
        if color == rl_color and move is not None and move["capture"] is not None:
            rl_captures += 1

            captured_color, captured_piece_id = move["capture"]
            captured_piece = state.pieces[captured_color][captured_piece_id]
            rl_capture_progress_total += captured_piece["progress"]

        apply_move(state, color, move)
        state.winner = check_winner(state)

        gets_extra_turn = move_lands_on_double_spot(state, move)

        if not gets_extra_turn:
            state.next_player()

        state.turn_count += 1

    # Count how many pieces the RL bot finished.
    rl_pieces_finished = sum(
        1
        for piece in state.pieces[rl_color].values()
        if piece["status"] == "DONE"
    )

    # Count total progress across the RL bot's pieces.
    rl_total_progress = sum(
        piece["progress"]
        for piece in state.pieces[rl_color].values()
    )

    # Final outcome reward.
    # Fine-tuning phase: winning matters much more than side objectives.
    if state.winner == rl_color:
        reward = 10.0
        won = True
    elif state.winner is None:
        reward = 0.0
        won = False
    else:
        reward = -10.0
        won = False

    # Fine-tuning intermediate rewards.
    # These are intentionally small compared to win/loss.
    finished_piece_reward = 0.25 * rl_pieces_finished
    progress_reward = 0.005 * (rl_total_progress / 28)

    # Captures are useful, but should not dominate the objective.
    capture_reward = 0.005 * rl_captures
    advanced_capture_reward = 0.001 * (rl_capture_progress_total / 28)

    reward += (
        finished_piece_reward
        + progress_reward
        + capture_reward
        + advanced_capture_reward
    )

    agent.end_episode(reward)

    return {
        "winner": state.winner,
        "rl_color": rl_color,
        "won": won,
        "reward": reward,
        "turns": state.turn_count,
        "rl_captures": rl_captures,
        "rl_capture_progress_total": rl_capture_progress_total,
        "rl_pieces_finished": rl_pieces_finished,
        "rl_total_progress": rl_total_progress,
    }


def train_rl_agent(
    batches=10,
    games_per_batch=100,
    learning_rate=0.1,
    opponent_strategy_name="double_capture_furthest",
    max_turns=1000,
    temperature=1.0,
    seed=None,
    save_path="results/rl/rl_weights.json",
    history_csv_path="results/rl/rl_training_history.csv",
    reset_history=False,
    load_existing_weights=True,
):
    """
    Train an RL bot in batches.

    This version appends training progress to a lifetime CSV.

    After each batch:
    - update weights
    - print batch win percentage
    - print average captures
    - print average reward
    - print average RL pieces finished
    - save batch history to CSV

    If reset_history=True, old training history is deleted and lifetime_batch
    starts again from 1.
    """

    import random
    from pathlib import Path

    if seed is not None:
        random.seed(seed)

    history_path = Path(history_csv_path)

    if reset_history and history_path.exists():
        history_path.unlink()

    run_id = make_run_id()
    last_lifetime_batch = get_last_lifetime_batch(history_csv_path)

    agent = RLAgent(
        training=True,
        temperature=temperature,
    )

    weights_path = Path(save_path)

    if load_existing_weights and weights_path.exists():
        agent.load_weights(save_path)
        print(f"Loaded existing weights from: {save_path}")
    else:
        print("Starting from default RL weights.")

    for batch_index in range(1, batches + 1):
        lifetime_batch = last_lifetime_batch + batch_index

        wins = 0
        total_turns = 0
        total_captures = 0
        total_reward = 0.0
        total_rl_pieces_finished = 0

        for _ in range(games_per_batch):
            result = simulate_training_game(
                agent=agent,
                opponent_strategy_name=opponent_strategy_name,
                max_turns=max_turns,
            )

            if result["won"]:
                wins += 1

            total_turns += result["turns"]
            total_captures += result["rl_captures"]
            total_reward += result["reward"]
            total_rl_pieces_finished += result["rl_pieces_finished"]

        win_rate = wins / games_per_batch
        avg_turns = total_turns / games_per_batch
        avg_captures = total_captures / games_per_batch
        avg_reward = total_reward / games_per_batch
        avg_rl_pieces_finished = total_rl_pieces_finished / games_per_batch

        agent.update_from_batch(learning_rate=learning_rate)
        agent.save_weights(save_path)

        row = {
            "run_id": run_id,
            "batch": batch_index,
            "lifetime_batch": lifetime_batch,
            "games_per_batch": games_per_batch,
            "opponent_strategy": opponent_strategy_name,
            "learning_rate": learning_rate,
            "temperature": temperature,
            "win_rate": win_rate,
            "avg_turns": avg_turns,
            "avg_captures": avg_captures,
            "avg_reward": avg_reward,
            "avg_rl_pieces_finished": avg_rl_pieces_finished,
        }

        for name, value in agent.pretty_weights().items():
            row[f"weight_{name}"] = value

        append_training_history_csv([row], history_csv_path)

        print("\n" + "-" * 60)
        print(f"Run ID: {run_id}")
        print(f"Batch {batch_index}/{batches}")
        print(f"Lifetime batch: {lifetime_batch}")
        print(f"Games: {games_per_batch}")
        print(f"Opponent strategy: {opponent_strategy_name}")
        print(f"Win rate: {win_rate * 100:.2f}%")
        print(f"Average turns: {avg_turns:.2f}")
        print(f"Average RL captures: {avg_captures:.2f}")
        print(f"Average reward: {avg_reward:.3f}")
        print(f"Average RL pieces finished: {avg_rl_pieces_finished:.2f}")
        print("Updated weights:")
        for name, value in agent.pretty_weights().items():
            print(f"  {name:24s}: {value: .4f}")

    print("\nTraining complete.")
    print(f"Saved weights to: {save_path}")
    print(f"Appended training history to: {history_csv_path}")

    return agent


def save_training_history_csv(history_rows, filename):
    """
    Save RL training progress to CSV.
    """
    import csv
    from pathlib import Path

    if not history_rows:
        return None

    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = list(history_rows[0].keys())

    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(history_rows)

    return path


