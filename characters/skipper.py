# skipper.py

from .base_character import Character
from power_system import PowerPhase

class Skipper(Character):
    """When anyone rolls a 1 for their main move, I go next in turn order."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roll == 1 and not self.finished:
            # Only trigger if someone ELSE rolled a 1 (not during our own turn)
            if roller != self:
                self.register_ability_use(game, play_by_play_lines, description="Skipper")
                play_by_play_lines.append(f"{self.name} ({self.piece}) will go next because {roller.name} rolled a 1!")

                # Queue Skipper to go after the current player's turn completes
                if not hasattr(game, 'queued_turns'):
                    game.queued_turns = []
                game.queued_turns.append(self)