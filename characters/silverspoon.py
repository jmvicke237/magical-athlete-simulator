# silverspoon.py

import config
from .base_character import Character
from power_system import PowerPhase

class SilverSpoon(Character):
    """I start on the space before the second corner. When I roll a 6, I move -6."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        # Start one space before the corner (matches Blimp's "second corner" reference).
        self.position = config.CORNER_POSITION - 1
        self.previous_position = self.position

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roller is self and roll == 6 and not self.finished:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) rolled a 6 — moves backwards 6 instead!"
            )
            # Skip the normal MOVEMENT phase; we move -6 directly here.
            self.skip_main_move = True
            self.move(game, play_by_play_lines, -6)
            self.register_ability_use(game, play_by_play_lines, description="SilverSpoon")
