# stinkeye.py

from .base_character import Character
from power_system import PowerPhase

class StinkEye(Character):
    """When other racers roll 3 for their main move, their final move (after any
    modifications) is reversed — they go backwards instead of forwards."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}
    EDITION = "v2"

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if (roller is not self and roll == 3
                and not self.finished and not roller.finished
                and roller not in game.eliminated_players):
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) gives {roller.name} ({roller.piece}) the "
                f"stink eye for rolling a 3 — their move will be reversed!"
            )
            # Mark the roller. base_character.take_turn applies the multiplier
            # after all ROLL_MODIFICATION runs, so any +/- modifiers (Coach,
            # Gunk, etc.) get negated together with the natural 3.
            roller.main_move_multiplier *= -1
            self.register_ability_use(game, play_by_play_lines, description="Stink Eye")
