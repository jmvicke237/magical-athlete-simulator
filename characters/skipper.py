# skipper.py

from .base_character import Character
from power_system import PowerPhase

class Skipper(Character):
    """When anyone rolls a 1 for their main move, I go next in turn order."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roll == 1 and not self.finished:
            # Only interrupt if someone ELSE rolled a 1 (not during our own turn)
            if roller != self:
                self.register_ability_use(game, play_by_play_lines, description="Skipper")
                play_by_play_lines.append(f"{self.name} ({self.piece}) goes next because {roller.name} rolled a 1!")

                # Take a full turn immediately
                self.take_turn(game, play_by_play_lines)

                # Set current player index to Skipper so next_player() advances from here
                # "Turn order continues to my left" = continues from after Skipper
                game.current_player_index = game.players.index(self)