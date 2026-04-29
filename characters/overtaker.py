# overtaker.py

from .base_character import Character
from power_system import PowerPhase

class Overtaker(Character):
    """I get +1 to my main move for each racer ahead of me."""

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}
    EDITION = "v2"

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        if other_player != self or self.finished:
            return roll

        racers_ahead = sum(
            1 for p in game.players
            if p is not self and not p.finished and p.position > self.position
        )

        if racers_ahead == 0:
            return roll

        modified_roll = roll + racers_ahead
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) gets +{racers_ahead} for racers ahead. "
            f"Move: {roll} -> {modified_roll}"
        )
        self.register_ability_use(game, play_by_play_lines, description="Overtaker")
        return modified_roll
