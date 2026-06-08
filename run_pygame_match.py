from viewers.pygame_viewer import watch_match


if __name__ == "__main__":
    watch_match(
        players=["Blue", "Red", "Green", "Yellow"],
        strategies_by_color={
            "Blue": "conservative",
            "Red": "conservative",
            "Green": "conservative",
            "Yellow": "conservative",
        },
        max_turns=1000,
    )