# characters/blimp.py

from .base_character import Character
from power_system import PowerPhase

class Blimp(Character):
    """When I start my turn before the second corner, I get +2. On or after that corner, I get -2."""

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Modifies the Blimp's roll based on its position."""
        if other_player == self:
            if self.turn_start_position < game.board.corner_position:
                modified_roll = roll + 2
                play_by_play_lines.append(f"{self.name} ({self.piece}) gets +2 to their roll (before corner). Roll: {roll} -> {modified_roll}")
            else:
                modified_roll = max(1, roll - 1)
                play_by_play_lines.append(f"{self.name} ({self.piece}) gets -1 to their roll (on or after corner). Roll: {roll} -> {modified_roll}")

            self.register_ability_use(game, play_by_play_lines, description="Blimp")
            return modified_roll

        return roll