import csv
from pathlib import Path

import matplotlib.pyplot as plt


# New bot history and plot output folder
HISTORY_CSV = "results/rl/rl_training_history_v2_danger_count_no_home.csv"
OUTPUT_DIR = "results/rl/plots_v2_danger_count_no_home"


def read_training_history(filename):
    path = Path(filename)

    if not path.exists():
        raise FileNotFoundError(
            f"Could not find {filename}. "
            "Make sure train_rl_bot.py is saving history to this same path."
        )

    rows = []

    with path.open("r") as file:
        reader = csv.DictReader(file)

        for row in reader:
            cleaned = {
                "run_id": row.get("run_id", ""),
                "batch": int(row["batch"]),
                "lifetime_batch": int(row.get("lifetime_batch", row["batch"])),
                "win_rate": float(row["win_rate"]),
                "avg_captures": float(row["avg_captures"]),
                "avg_reward": float(row["avg_reward"]),
                "avg_rl_pieces_finished": float(row["avg_rl_pieces_finished"]),
                "avg_turns": float(row["avg_turns"]),
            }

            # Automatically include all weight columns.
            for key, value in row.items():
                if key.startswith("weight_"):
                    cleaned[key] = float(value)

            rows.append(cleaned)

    return rows


def plot_metric(rows, metric, title, ylabel, output_filename):
    lifetime_batches = [row["lifetime_batch"] for row in rows]
    values = [row[metric] for row in rows]

    plt.figure(figsize=(9, 5))
    plt.plot(lifetime_batches, values, marker="o")
    plt.title(title)
    plt.xlabel("Lifetime Training Batch")
    plt.ylabel(ylabel)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = Path(OUTPUT_DIR) / output_filename
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Saved {output_path}")


def plot_weights(rows):
    lifetime_batches = [row["lifetime_batch"] for row in rows]

    weight_columns = [
        key
        for key in rows[0].keys()
        if key.startswith("weight_")
    ]

    if not weight_columns:
        print("No weight columns found. Skipping weight plot.")
        return

    plt.figure(figsize=(11, 6))

    for column in weight_columns:
        values = [row[column] for row in rows]
        label = column.replace("weight_", "")
        plt.plot(lifetime_batches, values, marker="o", label=label)

    plt.title("V2 RL Bot Training Progress: Weight Changes")
    plt.xlabel("Lifetime Training Batch")
    plt.ylabel("Weight Value")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = Path(OUTPUT_DIR) / "v2_weight_changes.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Saved {output_path}")


def plot_selected_weights(rows):
    """
    Cleaner plot for the most important V2 weights.

    V2 removed:
    - home_piece
    - lands_in_danger
    - escapes_danger

    V2 added:
    - current_danger_count
    - landing_danger_count
    - danger_reduction
    """
    lifetime_batches = [row["lifetime_batch"] for row in rows]

    selected = [
        "weight_finish",
        "weight_capture",
        "weight_double",
        "weight_progress",
        "weight_current_danger_count",
        "weight_landing_danger_count",
        "weight_danger_reduction",
        "weight_captured_piece_progress",
    ]

    available = [column for column in selected if column in rows[0]]

    if not available:
        print("No selected weight columns found. Skipping selected weight plot.")
        return

    plt.figure(figsize=(11, 6))

    for column in available:
        values = [row[column] for row in rows]
        label = column.replace("weight_", "")
        plt.plot(lifetime_batches, values, marker="o", label=label)

    plt.title("V2 RL Bot Training Progress: Selected Weight Changes")
    plt.xlabel("Lifetime Training Batch")
    plt.ylabel("Weight Value")
    plt.grid(True, alpha=0.3)
    plt.legend()
    plt.tight_layout()

    output_path = Path(OUTPUT_DIR) / "v2_selected_weight_changes.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Saved {output_path}")


def plot_run_markers(rows):
    """
    Shows which run each lifetime batch came from.
    """
    lifetime_batches = [row["lifetime_batch"] for row in rows]
    run_ids = [row["run_id"] for row in rows]

    unique_runs = []
    for run_id in run_ids:
        if run_id not in unique_runs:
            unique_runs.append(run_id)

    run_to_number = {
        run_id: index + 1
        for index, run_id in enumerate(unique_runs)
    }

    run_numbers = [run_to_number[run_id] for run_id in run_ids]

    plt.figure(figsize=(9, 4))
    plt.scatter(lifetime_batches, run_numbers)
    plt.title("V2 RL Training Runs Over Lifetime Batches")
    plt.xlabel("Lifetime Training Batch")
    plt.ylabel("Run Number")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()

    output_path = Path(OUTPUT_DIR) / "v2_run_markers.png"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=200)
    plt.close()

    print(f"Saved {output_path}")


def main():
    rows = read_training_history(HISTORY_CSV)

    if not rows:
        print("No training history rows found.")
        return

    plot_metric(
        rows,
        metric="win_rate",
        title="V2 RL Bot Training Progress: Win Rate",
        ylabel="Win Rate",
        output_filename="v2_win_rate.png",
    )

    plot_metric(
        rows,
        metric="avg_captures",
        title="V2 RL Bot Training Progress: Average Captures",
        ylabel="Average Captures per Game",
        output_filename="v2_avg_captures.png",
    )

    plot_metric(
        rows,
        metric="avg_reward",
        title="V2 RL Bot Training Progress: Average Reward",
        ylabel="Average Reward per Game",
        output_filename="v2_avg_reward.png",
    )

    plot_metric(
        rows,
        metric="avg_rl_pieces_finished",
        title="V2 RL Bot Training Progress: Average Pieces Finished",
        ylabel="Average RL Pieces Finished per Game",
        output_filename="v2_avg_pieces_finished.png",
    )

    plot_metric(
        rows,
        metric="avg_turns",
        title="V2 RL Bot Training Progress: Average Game Length",
        ylabel="Average Turns",
        output_filename="v2_avg_turns.png",
    )

    plot_weights(rows)
    plot_selected_weights(rows)
    plot_run_markers(rows)


if __name__ == "__main__":
    main()