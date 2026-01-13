# characters/alchemist.py

from .base_character import Character
from power_system import PowerPhase

class Alchemist(Character):
    """When I roll a 1 or 2 for my main move, I can move 4 instead."""

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}

    def __init__(self, name, piece):
        super().__init__(name, piece)

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Alchemist replaces their own roll of 1 or 2 with 4."""
        if other_player == self:
            # Check the original die roll (not the modified value)
            if self.last_roll in (1, 2):
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) uses Alchemist ability to move 4 instead. Roll: {self.last_roll} -> 4"
                )
                self.register_ability_use(game, play_by_play_lines, description="Alchemist")
                return 4
        return roll