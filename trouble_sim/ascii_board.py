"""ASCII board display helpers."""

from .constants import BOARD_SIZE


def get_piece_label(color, piece_id):
    return color[0].upper() + str(piece_id)


def get_board_labels(state):
    board = ["__" for _ in range(BOARD_SIZE)]

    for color, pieces in state.pieces.items():
        for piece_id, piece in pieces.items():
            if piece["status"] == "BOARD":
                position = piece["position"]
                board[position] = get_piece_label(color, piece_id)

    return board


def print_ascii_board(state):
    board = get_board_labels(state)

    print("\nASCII Board State")
    print("-----------------")

    print("        " + " ".join(f"{i:02}" for i in range(0, 7)))
    print("        " + " ".join(board[i] for i in range(0, 7)))

    print(f"   27 {board[27]}                 {board[7]} 07")
    print(f"   26 {board[26]}                 {board[8]} 08")
    print(f"   25 {board[25]}                 {board[9]} 09")
    print(f"   24 {board[24]}                 {board[10]} 10")
    print(f"   23 {board[23]}                 {board[11]} 11")
    print(f"   22 {board[22]}                 {board[12]} 12")

    print("        " + " ".join(f"{i:02}" for i in range(21, 13, -1)))
    print("        " + " ".join(board[i] for i in range(21, 13, -1)))

    print("\nHome Pieces:")
    for color in state.players:
        home_pieces = [
            get_piece_label(color, piece_id)
            for piece_id, piece in state.pieces[color].items()
            if piece["status"] == "HOME"
        ]
        print(f"{color}: {', '.join(home_pieces) if home_pieces else 'none'}")

    print("\nDone Pieces:")
    for color in state.players:
        done_pieces = [
            get_piece_label(color, piece_id)
            for piece_id, piece in state.pieces[color].items()
            if piece["status"] == "DONE"
        ]
        print(f"{color}: {', '.join(done_pieces) if done_pieces else 'none'}")
