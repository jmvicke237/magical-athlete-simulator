# skipper.py

from .base_character import Character
from power_system import PowerPhase

class Skipper(Character):
    """When anyone rolls a 1 for their main move, I go next in turn order."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roll == 1 and not self.finished:
            self.register_ability_use(game, play_by_play_lines, description="Skipper")
            game.change_turn_order(self, play_by_play_lines)