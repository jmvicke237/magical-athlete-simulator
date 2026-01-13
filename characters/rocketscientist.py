# rocketscientist.py

from .base_character import Character
from power_system import PowerPhase

class RocketScientist(Character):
    """When I roll for my main move, I can move double that number. If I do, I trip after moving."""

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}

    def __init__(self, name, piece):
        super().__init__(name, piece)

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Rocket Scientist doubles their own roll and trips after moving."""
        if other_player == self:
            doubled_roll = roll * 2
            # Will trip after movement completes
            self.tripped = True
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) doubles their roll to {doubled_roll} and will trip after moving!"
            )
            self.register_ability_use(game, play_by_play_lines, description="RocketScientist")
            return doubled_roll
        return roll