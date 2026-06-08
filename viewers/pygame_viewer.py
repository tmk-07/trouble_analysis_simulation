"""Pygame replay viewer for a single Trouble simulation.

Controls:
- RIGHT / SPACE: next move
- LEFT: previous move
- A: toggle autoplay
- R: simulate a new game with the same settings
- ESC / close window: quit
"""

import sys
from pathlib import Path

# Allow running this file directly: python viewers/pygame_viewer.py
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    import pygame
except ImportError as exc:
    raise SystemExit("pygame is not installed. Run: pip install pygame") from exc

from trouble_sim.constants import BOARD_SIZE, DOUBLE_SPOTS
from trouble_sim.replay import simulate_game_with_replay


# -----------------------------
# Window / layout constants
# -----------------------------

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 900
FPS = 60
AUTOPLAY_MS = 650

PADDING = 24
HEADER_HEIGHT = 112
FOOTER_HEIGHT = 48
SIDEBAR_WIDTH = 320
GAP = 18

BACKGROUND = (242, 244, 248)
PANEL = (248, 249, 252)
HEADER_PANEL = (228, 232, 240)
BORDER = (185, 191, 202)
TEXT = (35, 38, 45)
MUTED_TEXT = (92, 98, 110)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
SPACE_FILL = (255, 255, 255)
DOUBLE_FILL = (255, 232, 140)
CURRENT_HIGHLIGHT = (210, 226, 255)

COLOR_RGB = {
    "Blue": (55, 110, 235),
    "Red": (220, 65, 65),
    "Green": (70, 170, 95),
    "Yellow": (225, 190, 45),
}


# -----------------------------
# Layout helpers
# -----------------------------

def get_layout_rects():
    """Return the fixed screen regions used by the viewer."""
    header_rect = pygame.Rect(
        PADDING,
        PADDING,
        WINDOW_WIDTH - 2 * PADDING,
        HEADER_HEIGHT,
    )

    footer_rect = pygame.Rect(
        PADDING,
        WINDOW_HEIGHT - FOOTER_HEIGHT - PADDING,
        WINDOW_WIDTH - 2 * PADDING,
        FOOTER_HEIGHT,
    )

    board_rect = pygame.Rect(
        PADDING,
        header_rect.bottom + GAP,
        WINDOW_WIDTH - SIDEBAR_WIDTH - 3 * PADDING - GAP,
        footer_rect.top - (header_rect.bottom + GAP) - GAP,
    )

    sidebar_rect = pygame.Rect(
        board_rect.right + GAP,
        board_rect.top,
        SIDEBAR_WIDTH,
        board_rect.height,
    )

    return header_rect, board_rect, sidebar_rect, footer_rect


def build_space_coords(board_rect):
    """Create a rectangular loop coordinate map for 28 board spaces.

    The board is drawn inside board_rect, leaving enough space for labels.
    This avoids overlap with the header, sidebar, and footer.
    """
    coords = {}

    left_x = board_rect.left + 85
    right_x = board_rect.right - 85
    top_y = board_rect.top + 60
    bottom_y = board_rect.bottom - 75

    width = right_x - left_x
    height = bottom_y - top_y

    # Top row: positions 0-6, left to right.
    for i in range(7):
        x = left_x + i * width / 6
        coords[i] = (int(x), int(top_y))

    # Right side: positions 7-13, top to bottom, not using the exact corner.
    for i in range(7):
        y = top_y + (i + 1) * height / 8
        coords[7 + i] = (int(right_x), int(y))

    # Bottom row: positions 14-21, right to left.
    for i in range(8):
        x = right_x - i * width / 7
        coords[14 + i] = (int(x), int(bottom_y))

    # Left side: positions 22-27, bottom to top, not using exact corners.
    for i in range(6):
        y = bottom_y - (i + 1) * height / 7
        coords[22 + i] = (int(left_x), int(y))

    return coords


def build_fonts():
    return {
        "title": pygame.font.SysFont("arial", 26, bold=True),
        "section": pygame.font.SysFont("arial", 21, bold=True),
        "info": pygame.font.SysFont("arial", 17),
        "small": pygame.font.SysFont("arial", 15),
        "label": pygame.font.SysFont("arial", 14),
        "piece": pygame.font.SysFont("arial", 14, bold=True),
    }


# -----------------------------
# Text helpers
# -----------------------------

def draw_text(screen, font, text, x, y, color=TEXT):
    surface = font.render(str(text), True, color)
    screen.blit(surface, (x, y))
    return surface.get_rect(topleft=(x, y))


def draw_wrapped_text(screen, font, text, x, y, max_width, color=TEXT, line_spacing=4):
    """Draw simple word-wrapped text and return the next y position."""
    words = str(text).split()
    if not words:
        return y

    line = ""
    for word in words:
        test = word if not line else f"{line} {word}"
        if font.size(test)[0] <= max_width:
            line = test
        else:
            draw_text(screen, font, line, x, y, color)
            y += font.get_height() + line_spacing
            line = word

    if line:
        draw_text(screen, font, line, x, y, color)
        y += font.get_height() + line_spacing

    return y


def piece_label(color, piece_id):
    return f"{color[0].upper()}{piece_id}"


def get_move_text(frame):
    return frame.get("move_description") or "Initial board state"


# -----------------------------
# Drawing functions
# -----------------------------

def draw_header(screen, fonts, header_rect, frame_index, total_frames, frame, autoplay):
    pygame.draw.rect(screen, HEADER_PANEL, header_rect, border_radius=14)
    pygame.draw.rect(screen, BORDER, header_rect, 2, border_radius=14)

    title = f"Trouble Replay | Move {frame_index}/{total_frames - 1}"
    draw_text(screen, fonts["title"], title, header_rect.x + 18, header_rect.y + 12)

    player = frame.get("player") or "None"
    roll = frame.get("roll") if frame.get("roll") is not None else "-"
    extra = "Yes" if frame.get("extra_turn") else "No"
    winner = frame.get("winner") or "None"
    autoplay_text = "On" if autoplay else "Off"

    details = (
        f"Player: {player}    Roll: {roll}    "
        f"Extra turn: {extra}    Winner: {winner}    Autoplay: {autoplay_text}"
    )
    draw_text(screen, fonts["info"], details, header_rect.x + 18, header_rect.y + 48, MUTED_TEXT)

    move_text = f"Move: {get_move_text(frame)}"
    draw_wrapped_text(
        screen,
        fonts["small"],
        move_text,
        header_rect.x + 18,
        header_rect.y + 76,
        header_rect.width - 36,
        TEXT,
        line_spacing=2,
    )


def draw_footer(screen, fonts, footer_rect):
    pygame.draw.rect(screen, HEADER_PANEL, footer_rect, border_radius=12)
    pygame.draw.rect(screen, BORDER, footer_rect, 2, border_radius=12)

    controls = "SPACE/RIGHT: next    LEFT: previous    A: autoplay    R: new game    ESC: quit"
    text_surface = fonts["small"].render(controls, True, MUTED_TEXT)
    text_rect = text_surface.get_rect(center=footer_rect.center)
    screen.blit(text_surface, text_rect)


def draw_board_panel(screen, board_rect):
    pygame.draw.rect(screen, PANEL, board_rect, border_radius=16)
    pygame.draw.rect(screen, BORDER, board_rect, 2, border_radius=16)


def draw_board_spaces(screen, fonts, coords, current_move=None):
    # Highlight the destination of the current move, if there is one.
    highlighted_position = None
    if current_move is not None:
        highlighted_position = current_move.get("to_position")

    for pos in range(BOARD_SIZE):
        x, y = coords[pos]
        fill = DOUBLE_FILL if pos in DOUBLE_SPOTS else SPACE_FILL

        if highlighted_position == pos:
            pygame.draw.circle(screen, CURRENT_HIGHLIGHT, (x, y), 38)

        pygame.draw.circle(screen, fill, (x, y), 30)
        pygame.draw.circle(screen, MUTED_TEXT, (x, y), 30, 2)

        if pos in DOUBLE_SPOTS:
            d_surface = fonts["section"].render("D", True, TEXT)
            d_rect = d_surface.get_rect(center=(x, y))
            screen.blit(d_surface, d_rect)

        pos_surface = fonts["label"].render(str(pos), True, TEXT)
        pos_rect = pos_surface.get_rect(center=(x, y + 42))
        screen.blit(pos_surface, pos_rect)


def draw_pieces_on_board(screen, fonts, coords, pieces):
    # Group pieces by position. Current rules do not stack pieces, but this makes
    # the viewer safer for future variants.
    by_position = {}
    for color, color_pieces in pieces.items():
        for piece_id, piece in color_pieces.items():
            if piece["status"] == "BOARD":
                position = int(piece["position"])
                by_position.setdefault(position, []).append((color, int(piece_id)))

    offsets = [(-13, -13), (13, -13), (-13, 13), (13, 13)]

    for position, occupants in by_position.items():
        base_x, base_y = coords[position]
        for index, (color, piece_id) in enumerate(occupants):
            dx, dy = offsets[index % len(offsets)]
            x, y = base_x + dx, base_y + dy

            pygame.draw.circle(screen, COLOR_RGB[color], (x, y), 16)
            pygame.draw.circle(screen, BLACK, (x, y), 16, 1)

            label = fonts["piece"].render(str(piece_id), True, WHITE)
            label_rect = label.get_rect(center=(x, y))
            screen.blit(label, label_rect)


def draw_sidebar(screen, fonts, sidebar_rect, frame):
    pygame.draw.rect(screen, PANEL, sidebar_rect, border_radius=16)
    pygame.draw.rect(screen, BORDER, sidebar_rect, 2, border_radius=16)

    snapshot = frame["snapshot"]
    players = snapshot["players"]
    pieces = snapshot["pieces"]

    x = sidebar_rect.x + 18
    y = sidebar_rect.y + 18

    draw_text(screen, fonts["section"], "Home / Done", x, y)
    y += 42

    for color in players:
        pygame.draw.circle(screen, COLOR_RGB[color], (x + 12, y + 13), 12)
        draw_text(screen, fonts["section"], color, x + 34, y + 1)
        y += 30

        home = []
        done = []
        for piece_id, piece in pieces[color].items():
            label = piece_label(color, piece_id)
            if piece["status"] == "HOME":
                home.append(label)
            elif piece["status"] == "DONE":
                done.append(label)

        home_text = "Home: " + (", ".join(home) if home else "none")
        done_text = "Done:  " + (", ".join(done) if done else "none")

        y = draw_wrapped_text(screen, fonts["info"], home_text, x, y, sidebar_rect.width - 36, TEXT)
        y = draw_wrapped_text(screen, fonts["info"], done_text, x, y, sidebar_rect.width - 36, TEXT)
        y += 22

    # Move details near the bottom of the sidebar.
    details_top = sidebar_rect.bottom - 145
    pygame.draw.line(screen, BORDER, (x, details_top), (sidebar_rect.right - 18, details_top), 2)
    draw_text(screen, fonts["section"], "Current Move", x, details_top + 16)
    draw_wrapped_text(
        screen,
        fonts["info"],
        get_move_text(frame),
        x,
        details_top + 48,
        sidebar_rect.width - 36,
        TEXT,
    )


def draw_replay_frame(screen, fonts, replay, frame_index, autoplay):
    frame = replay[frame_index]
    snapshot = frame["snapshot"]
    pieces = snapshot["pieces"]

    header_rect, board_rect, sidebar_rect, footer_rect = get_layout_rects()
    coords = build_space_coords(board_rect)

    screen.fill(BACKGROUND)

    draw_header(screen, fonts, header_rect, frame_index, len(replay), frame, autoplay)
    draw_board_panel(screen, board_rect)
    draw_board_spaces(screen, fonts, coords, frame.get("chosen_move"))
    draw_pieces_on_board(screen, fonts, coords, pieces)
    draw_sidebar(screen, fonts, sidebar_rect, frame)
    draw_footer(screen, fonts, footer_rect)


# -----------------------------
# Public function
# -----------------------------

def watch_match(
    players=("Blue", "Green"),
    strategies_by_color=None,
    max_turns=1000,
    seed=None,
):
    """Simulate one game and open a Pygame replay viewer.

    Example:
        watch_match(
            players=["Blue", "Green"],
            strategies_by_color={"Blue": "furthest", "Green": "random"},
        )
    """
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Trouble Strategy Simulator Replay")
    clock = pygame.time.Clock()
    fonts = build_fonts()

    def new_replay():
        return simulate_game_with_replay(
            players=list(players),
            strategies_by_color=strategies_by_color,
            max_turns=max_turns,
            seed=seed,
        )[2]

    replay = new_replay()
    frame_index = 0
    autoplay = False
    last_advance = pygame.time.get_ticks()
    running = True

    while running:
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in (pygame.K_SPACE, pygame.K_RIGHT):
                    frame_index = min(frame_index + 1, len(replay) - 1)
                elif event.key == pygame.K_LEFT:
                    frame_index = max(frame_index - 1, 0)
                elif event.key == pygame.K_a:
                    autoplay = not autoplay
                    last_advance = now
                elif event.key == pygame.K_r:
                    replay = new_replay()
                    frame_index = 0
                    autoplay = False

        if autoplay and now - last_advance >= AUTOPLAY_MS:
            frame_index = min(frame_index + 1, len(replay) - 1)
            last_advance = now
            if frame_index == len(replay) - 1:
                autoplay = False

        draw_replay_frame(screen, fonts, replay, frame_index, autoplay)
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


from trouble_sim.rl_agent import RLAgent

if __name__ == "__main__":
    trained_bot = RLAgent(training=False)
    trained_bot.load_weights("results/rl/rl_weights.json")
    watch_match(
        players=["Blue", "Red", "Green", "Yellow"],
        strategies_by_color={
            "Blue": trained_bot,
            "Red": "double_capture_furthest",
            "Green": "double_capture_furthest",
            "Yellow": "double_capture_furthest",
        },
        max_turns=1000,
    )