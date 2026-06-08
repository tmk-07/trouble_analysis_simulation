"""Constants for the Trouble simulator."""

COLORS = ["Blue", "Red", "Green", "Yellow"]

NUM_PIECES_PER_PLAYER = 4
BOARD_SIZE = 28

# Each color's fixed entry/start position on the main board.
START_POSITIONS = {
    "Blue": 0,
    "Red": 7,
    "Green": 14,
    "Yellow": 21,
}

# Spaces where landing grants an extra turn.
DOUBLE_SPOTS = {3, 10, 17, 24}
