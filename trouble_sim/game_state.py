"""Game state model for the Trouble simulator."""

from copy import deepcopy

from .constants import DOUBLE_SPOTS, NUM_PIECES_PER_PLAYER, START_POSITIONS


def validate_players(players):
    """Validate player colors and basic matchup setup."""
    if not players:
        raise ValueError("You must provide at least one player.")

    if len(players) != len(set(players)):
        raise ValueError(f"Duplicate players are not allowed: {players}")

    for color in players:
        if color not in START_POSITIONS:
            valid = ", ".join(START_POSITIONS.keys())
            raise ValueError(f"Invalid color: {color}. Choose from: {valid}.")


class GameState:
    """Stores the complete state of a single game."""

    def __init__(self, players):
        validate_players(players)

        self.players = list(players)
        self.current_player_index = 0

        self.pieces = {
            color: {
                piece_id: {
                    "status": "HOME",   # HOME, BOARD, DONE
                    "position": None,   # board index if on board
                    "progress": 0,      # total spaces traveled
                }
                for piece_id in range(NUM_PIECES_PER_PLAYER)
            }
            for color in players
        }

        self.double_spots = set(DOUBLE_SPOTS)
        self.start_positions = {color: START_POSITIONS[color] for color in players}
        self.winner = None
        self.turn_count = 0

    def copy(self):
        return deepcopy(self)

    def current_player(self):
        return self.players[self.current_player_index]

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.players)

    def print_state(self):
        print(f"\nTurn {self.turn_count}")
        print(f"Current player: {self.current_player()}")
        for color in self.players:
            print(color, self.pieces[color])
