"""Core game engine: dice, legal moves, move application, and game simulation."""

import random

from .constants import BOARD_SIZE
from .game_state import GameState
from .strategies import STRATEGIES, strategy_furthest


def roll_dice():
    return random.randint(1, 6)


def get_occupied_positions(state):
    """
    Return a mapping of board_position -> (color, piece_id).
    Only pieces currently on the main board are included.
    """
    occupied = {}

    for color, pieces in state.pieces.items():
        for piece_id, piece in pieces.items():
            if piece["status"] == "BOARD":
                occupied[piece["position"]] = (color, piece_id)

    return occupied

def move_lands_on_double_spot(state, move):
    """
    Returns True if the chosen move lands on a double spot.
    Finishing a piece does not count because to_position is None.
    """
    return (
        move is not None
        and move.get("to_position") is not None
        and move["to_position"] in state.double_spots
    )

def get_legal_moves(state, color, roll):
    legal_moves = []
    occupied = get_occupied_positions(state)

    for piece_id, piece in state.pieces[color].items():
        status = piece["status"]

        if status == "DONE":
            continue

        # -------------------------------------------------
        # Piece leaving HOME.
        # In this simplified model, no 6 is required.
        #
        # The roll is used immediately:
        # roll 1 -> start position
        # roll 2 -> start position + 1
        # roll 4 -> start position + 3
        #
        # Example for Blue:
        # start = 0, roll = 4 -> position 3
        # -------------------------------------------------
        if status == "HOME":
            destination = (state.start_positions[color] + roll - 1) % BOARD_SIZE
            new_progress = roll

            if destination in occupied:
                occupying_color, occupying_piece = occupied[destination]

                # Cannot land on your own piece.
                if occupying_color == color:
                    continue

                capture = (occupying_color, occupying_piece)
            else:
                capture = None

            legal_moves.append({
                "piece_id": piece_id,
                "from_status": "HOME",
                "from_position": None,
                "to_status": "BOARD",
                "to_position": destination,
                "new_progress": new_progress,
                "capture": capture,
            })

        # -------------------------------------------------
        # Piece already on BOARD.
        # -------------------------------------------------
        elif status == "BOARD":
            current_position = piece["position"]
            current_progress = piece["progress"]
            new_progress = current_progress + roll

            # Simplified finish rule:
            # progress 1  = first board space
            # progress 28 = last board space
            # progress 29+ = DONE
            if new_progress > BOARD_SIZE:
                legal_moves.append({
                    "piece_id": piece_id,
                    "from_status": "BOARD",
                    "from_position": current_position,
                    "to_status": "DONE",
                    "to_position": None,
                    "new_progress": new_progress,
                    "capture": None,
                })
            else:
                destination = (current_position + roll) % BOARD_SIZE

                if destination in occupied:
                    occupying_color, occupying_piece = occupied[destination]

                    # Cannot land on your own piece.
                    if occupying_color == color:
                        continue

                    capture = (occupying_color, occupying_piece)
                else:
                    capture = None

                legal_moves.append({
                    "piece_id": piece_id,
                    "from_status": "BOARD",
                    "from_position": current_position,
                    "to_status": "BOARD",
                    "to_position": destination,
                    "new_progress": new_progress,
                    "capture": capture,
                })

    return legal_moves


def apply_move(state, color, move):
    if move is None:
        return

    piece_id = move["piece_id"]

    # Handle capture.
    if move["capture"] is not None:
        captured_color, captured_piece = move["capture"]
        state.pieces[captured_color][captured_piece]["status"] = "HOME"
        state.pieces[captured_color][captured_piece]["position"] = None
        state.pieces[captured_color][captured_piece]["progress"] = 0

    # Move current player's piece.
    state.pieces[color][piece_id]["status"] = move["to_status"]
    state.pieces[color][piece_id]["position"] = move["to_position"]
    state.pieces[color][piece_id]["progress"] = move["new_progress"]


def check_winner(state):
    for color in state.players:
        if all(piece["status"] == "DONE" for piece in state.pieces[color].values()):
            return color
    return None


def normalize_strategies(players, strategies_by_color=None, default_strategy=strategy_furthest):
    """
    Build a color -> strategy function dictionary.

    strategies_by_color can contain either:
    - strategy functions directly
    - string names from STRATEGIES, such as "furthest"
    """
    strategies_by_color = strategies_by_color or {}
    normalized = {}

    for color in players:
        strategy = strategies_by_color.get(color, default_strategy)

        if isinstance(strategy, str):
            if strategy not in STRATEGIES:
                valid = ", ".join(STRATEGIES.keys())
                raise ValueError(f"Unknown strategy '{strategy}'. Choose from: {valid}.")
            strategy = STRATEGIES[strategy]

        normalized[color] = strategy

    return normalized


def simulate_game(players, strategies_by_color=None, max_turns=1000, verbose=False):
    state = GameState(players)
    strategies = normalize_strategies(players, strategies_by_color)

    while state.winner is None and state.turn_count < max_turns:
        color = state.current_player()

        if verbose:
            state.print_state()

        roll = roll_dice()

        if verbose:
            print(f"{color} rolled a {roll}")

        legal_moves = get_legal_moves(state, color, roll)
        move = strategies[color](state, color, roll, legal_moves)

        if verbose:
            print(f"Legal moves: {legal_moves}")
            print(f"Chosen move: {move}")

        apply_move(state, color, move)
        state.winner = check_winner(state)

        landed_on_double_spot = move_lands_on_double_spot(state, move)

        # Extra turn only when landing on a double spot.
        gets_extra_turn = landed_on_double_spot

        if not gets_extra_turn:
            state.next_player()

        state.turn_count += 1

    return state.winner, state