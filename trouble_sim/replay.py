"""Replay helpers for simulating and reviewing one full game turn by turn."""

from copy import deepcopy
import json
from pathlib import Path
import random

from .engine import (
    roll_dice,
    get_legal_moves,
    apply_move,
    check_winner,
    normalize_strategies,
    move_lands_on_double_spot,
)
from .game_state import GameState


def snapshot_state(state):
    """Return a JSON-friendly snapshot of the current game state."""
    return {
        "players": list(state.players),
        "current_player_index": state.current_player_index,
        "current_player": state.current_player(),
        "pieces": deepcopy(state.pieces),
        "winner": state.winner,
        "turn_count": state.turn_count,
    }


def describe_move(color, move):
    """Create a short human-readable move description."""
    if move is None:
        return f"{color} has no legal move"

    piece = f"{color[0].upper()}{move['piece_id']}"
    from_pos = move["from_position"] if move["from_position"] is not None else move["from_status"]
    to_pos = move["to_position"] if move["to_position"] is not None else move["to_status"]

    text = f"{piece}: {from_pos} -> {to_pos}"

    if move.get("capture") is not None:
        captured_color, captured_piece = move["capture"]
        text += f" | captured {captured_color[0].upper()}{captured_piece}"

    if move.get("to_status") == "DONE":
        text += " | finished"

    return text


def simulate_game_with_replay(
    players,
    strategies_by_color=None,
    max_turns=1000,
    seed=None,
):
    """
    Simulate one game and return (winner, final_state, replay_frames).

    Each replay frame contains a board snapshot after a turn is completed.
    Frame 0 is the initial board before any move happens.
    """
    if seed is not None:
        random.seed(seed)

    state = GameState(players)
    strategies = normalize_strategies(players, strategies_by_color)

    replay = [
        {
            "frame_type": "initial",
            "turn": 0,
            "player": None,
            "roll": None,
            "legal_moves": [],
            "chosen_move": None,
            "move_description": "Initial board state",
            "captured": None,
            "landed_on_double_spot": False,
            "extra_turn": False,
            "winner": None,
            "snapshot": snapshot_state(state),
        }
    ]

    while state.winner is None and state.turn_count < max_turns:
        color = state.current_player()
        roll = roll_dice()
        legal_moves = get_legal_moves(state, color, roll)
        move = strategies[color](state, color, roll, legal_moves)

        apply_move(state, color, move)
        state.winner = check_winner(state)

        landed_on_double_spot = move_lands_on_double_spot(state, move)

        # Extra turn only when landing on a double spot.
        gets_extra_turn = landed_on_double_spot

        frame = {
            "frame_type": "turn",
            "turn": state.turn_count + 1,
            "player": color,
            "roll": roll,
            "legal_moves": deepcopy(legal_moves),
            "chosen_move": deepcopy(move),
            "move_description": describe_move(color, move),
            "captured": deepcopy(move["capture"]) if move is not None else None,
            "landed_on_double_spot": landed_on_double_spot,
            "extra_turn": gets_extra_turn,
            "winner": state.winner,
            "snapshot": snapshot_state(state),
        }
        replay.append(frame)

        if not gets_extra_turn:
            state.next_player()

        state.turn_count += 1

    return state.winner, state, replay

def save_replay(replay, filename):
    """Save replay frames as JSON."""
    path = Path(filename)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w") as file:
        json.dump(replay, file, indent=2)
    return path


def load_replay(filename):
    """Load replay frames from JSON."""
    with Path(filename).open("r") as file:
        return json.load(file)
