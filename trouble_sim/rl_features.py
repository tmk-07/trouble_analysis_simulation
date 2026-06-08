"""Feature extraction for reinforcement-learning strategies."""

from .constants import BOARD_SIZE


FEATURE_NAMES = [
    "finish",
    "capture",
    "double",
    "progress",

    # Better danger-count features
    "current_danger_count",
    "landing_danger_count",
    "danger_reduction",

    "captured_piece_progress",
]


def build_danger_map(state, color):
    """
    Build a map of positions that are dangerous for this color.

    A position is dangerous if an opponent piece could land on it with
    a roll from 1 to 6.

    Returns:
        {
            position: [
                {
                    "opponent": "Red",
                    "piece_id": 2,
                    "roll": 4
                },
                ...
            ]
        }
    """

    danger_map = {}

    for opponent in state.players:
        if opponent == color:
            continue

        for opponent_piece_id, opponent_piece in state.pieces[opponent].items():
            if opponent_piece["status"] != "BOARD":
                continue

            opponent_position = opponent_piece["position"]

            for roll in range(1, 7):
                dangerous_position = (opponent_position + roll) % BOARD_SIZE

                danger_map.setdefault(dangerous_position, []).append(
                    {
                        "opponent": opponent,
                        "piece_id": opponent_piece_id,
                        "roll": roll,
                    }
                )

    return danger_map


def count_threatening_pieces(danger_map, position):
    """
    Return how many unique opponent pieces could capture a piece on this position.

    We count unique opponent pieces, not number of dice rolls.

    Example:
        If Red piece 0 can capture this spot with roll 3,
        and Green piece 2 can capture this spot with roll 5,
        then danger count = 2.
    """

    if position is None:
        return 0

    threats = danger_map.get(position, [])

    unique_threatening_pieces = {
        (threat["opponent"], threat["piece_id"])
        for threat in threats
    }

    return len(unique_threatening_pieces)


def extract_move_features(state, color, move):
    """
    Convert a legal move into numeric features.

    These features are intentionally simple and interpretable.
    """

    features = {name: 0.0 for name in FEATURE_NAMES}

    if move is None:
        return features

    piece_id = move["piece_id"]
    piece = state.pieces[color][piece_id]

    to_position = move["to_position"]
    from_position = move["from_position"]

    danger_map = build_danger_map(state, color)

    current_danger_count = 0
    if piece["status"] == "BOARD":
        current_danger_count = count_threatening_pieces(danger_map, from_position)

    landing_danger_count = count_threatening_pieces(danger_map, to_position)

    is_finish = move["to_status"] == "DONE"
    is_capture = move["capture"] is not None
    is_double = (
        to_position is not None
        and to_position in state.double_spots
    )
  #  is_home_piece = piece["status"] == "HOME"

    lands_in_danger = landing_danger_count > 0
    escapes_danger = current_danger_count > 0 and landing_danger_count == 0

    features["finish"] = 1.0 if is_finish else 0.0
    features["capture"] = 1.0 if is_capture else 0.0
    features["double"] = 1.0 if is_double else 0.0
    features["progress"] = move["new_progress"] / BOARD_SIZE
    #features["home_piece"] = 1.0 if is_home_piece else 0.0

    # New count-based danger features.
    # Divide by 6 to keep values roughly small/normalized.
    features["current_danger_count"] = current_danger_count / 6
    features["landing_danger_count"] = landing_danger_count / 6
    features["danger_reduction"] = (current_danger_count - landing_danger_count) / 6

    if is_capture:
        captured_color, captured_piece_id = move["capture"]
        captured_piece = state.pieces[captured_color][captured_piece_id]
        features["captured_piece_progress"] = captured_piece["progress"] / BOARD_SIZE

    return features