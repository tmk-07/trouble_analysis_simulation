"""Move-selection strategies for the Trouble simulator."""

import random
from .constants import BOARD_SIZE


def build_danger_map(state, color):
    """
    Build a map of dangerous board positions for the given color.

    A position is dangerous if an opponent could land on it with a roll
    from 1 to 6 on their next move.

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

            for possible_roll in range(1, 7):
                dangerous_position = (opponent_position + possible_roll) % BOARD_SIZE

                if dangerous_position not in danger_map:
                    danger_map[dangerous_position] = []

                danger_map[dangerous_position].append({
                    "opponent": opponent,
                    "piece_id": opponent_piece_id,
                    "roll": possible_roll,
                })

    return danger_map


def is_piece_in_danger(state, color, piece_id, danger_map=None):
    """
    Return True if one of this player's pieces is currently on a dangerous square.
    """

    piece = state.pieces[color][piece_id]

    if piece["status"] != "BOARD":
        return False

    if danger_map is None:
        danger_map = build_danger_map(state, color)

    return piece["position"] in danger_map


def captured_piece_was_threatening_us(state, color, move):
    """
    Return True if the captured opponent piece was creating danger
    for any of our current pieces.

    This makes conservative play value captures that remove immediate threats.
    """

    if move["capture"] is None:
        return False

    captured_color, captured_piece_id = move["capture"]
    captured_piece = state.pieces[captured_color][captured_piece_id]

    if captured_piece["status"] != "BOARD":
        return False

    captured_position = captured_piece["position"]

    dangerous_positions_from_captured_piece = {
        (captured_position + possible_roll) % BOARD_SIZE
        for possible_roll in range(1, 7)
    }

    for my_piece in state.pieces[color].values():
        if my_piece["status"] != "BOARD":
            continue

        if my_piece["position"] in dangerous_positions_from_captured_piece:
            return True

    return False


def strategy_conservative(state, color, roll, legal_moves):
    """
    Conservative strategy.

    Priority idea:
    - Finish whenever possible.
    - Escape danger.
    - Avoid moving into danger.
    - Capture pieces that threaten us.
    - Capture generally.
    - Land on double spots only after safety/capture concerns.
    - Use progress as a tie-breaker.

    This is a scored heuristic, not a strict priority list.
    """

    if not legal_moves:
        return None

    danger_map = build_danger_map(state, color)
    dangerous_positions = set(danger_map.keys())

    best_move = None
    best_score = float("-inf")

    for move in legal_moves:
        score = 0

        piece_id = move["piece_id"]
        piece = state.pieces[color][piece_id]

        from_position = move["from_position"]
        to_position = move["to_position"]

        starts_in_danger = (
            piece["status"] == "BOARD"
            and from_position in dangerous_positions
        )

        lands_in_danger = (
            to_position is not None
            and to_position in dangerous_positions
        )

        lands_on_double = (
            to_position is not None
            and to_position in state.double_spots
        )

        # 1. Finishing is the most important.
        if move["to_status"] == "DONE":
            score += 10000

        # 2. Reward escaping danger.
        if starts_in_danger and not lands_in_danger:
            score += 2500

        # 3. Strongly avoid landing in danger.
        if lands_in_danger:
            score -= 1800
        else:
            score += 700

        # 4. Captures are good, especially if they remove a threat.
        if move["capture"] is not None:
            score += 600

            if captured_piece_was_threatening_us(state, color, move):
                score += 1200

        # 5. Double spots are useful, but not above safety.
        if lands_on_double:
            score += 300

        # 6. Prefer making progress as a tie-breaker.
        score += move["new_progress"]

        # 7. Slightly prefer moving a piece that is already farther along.
        if piece["status"] == "BOARD":
            score += piece["progress"] * 0.1

        if score > best_score:
            best_score = score
            best_move = move

    return best_move

def strategy_random(state, color, roll, legal_moves):
    """Choose a random legal move."""
    if not legal_moves:
        return None
    return random.choice(legal_moves)


def strategy_furthest(state, color, roll, legal_moves):
    """
    Choose the legal move for the piece that is furthest along.

    HOME pieces have progress -1.
    BOARD pieces use their current progress.
    DONE pieces are not included in legal moves.
    """
    if not legal_moves:
        return None

    def progress_score(move):
        piece_id = move["piece_id"]
        piece = state.pieces[color][piece_id]

        if piece["status"] == "HOME":
            return -1

        return piece["progress"]

    return max(legal_moves, key=progress_score)

def strategy_capture_first(state, color, roll, legal_moves):
    """
    Strategy:
    1. Finish if possible.
    2. Capture if possible.
    3. Otherwise move the furthest piece.
    """

    if not legal_moves:
        return None

    finishing_moves = [
        move for move in legal_moves
        if move["to_status"] == "DONE"
    ]

    if finishing_moves:
        return finishing_moves[0]

    capture_moves = [
        move for move in legal_moves
        if move["capture"] is not None
    ]

    if capture_moves:
        return capture_moves[0]

    return strategy_furthest(state, color, roll, legal_moves)

def strategy_double_capture_furthest(state, color, roll, legal_moves):
    """
    Strategy priority:
    1. Land on a double spot if possible.
    2. Capture an opponent if possible.
    3. Otherwise move the furthest-along piece.
    """

    if not legal_moves:
        return None

    # 1. Double spot first
    double_spot_moves = [
        move for move in legal_moves
        if move["to_position"] is not None
        and move["to_position"] in state.double_spots
    ]

    if double_spot_moves:
        return strategy_furthest(state, color, roll, double_spot_moves)

    # 2. Capture second
    capture_moves = [
        move for move in legal_moves
        if move["capture"] is not None
    ]

    if capture_moves:
        return strategy_furthest(state, color, roll, capture_moves)

    # 3. Furthest piece last
    return strategy_furthest(state, color, roll, legal_moves)

def strategy_capture_double_furthest(state, color, roll, legal_moves):
    """
    Strategy priority:
    1. Capture an opponent if possible.
    2. Land on a double spot if possible.
    3. Otherwise move the furthest-along piece.
    """

    if not legal_moves:
        return None

    # 1. Capture first
    capture_moves = [
        move for move in legal_moves
        if move["capture"] is not None
    ]

    if capture_moves:
        return strategy_furthest(state, color, roll, capture_moves)

    # 2. Double spot second
    double_spot_moves = [
        move for move in legal_moves
        if move["to_position"] is not None
        and move["to_position"] in state.double_spots
    ]

    if double_spot_moves:
        return strategy_furthest(state, color, roll, double_spot_moves)

    # 3. Furthest piece last
    return strategy_furthest(state, color, roll, legal_moves)


STRATEGIES = {
    "random": strategy_random,
    "furthest": strategy_furthest,
    "capture_first": strategy_capture_first,
    "double_capture_furthest": strategy_double_capture_furthest,
    "capture_double_furthest": strategy_capture_double_furthest,
    "conservative": strategy_conservative,
}
