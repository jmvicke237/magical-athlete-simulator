# lackey.py

from .base_character import Character
from power_system import PowerPhase

class Lackey(Character):
    """When another racer rolls a 6 for their main move, I move 2 before they move."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        """When another racer rolls a 6 for their main move, Lackey moves 2 spaces before they move."""
        if roller != self and roll == 6 and not self.finished:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moves 2 because {roller.name} ({roller.piece}) rolled a 6!"
            )
            self.move(game, play_by_play_lines, 2)
            self.register_ability_use(game, play_by_play_lines, description="Lackey")