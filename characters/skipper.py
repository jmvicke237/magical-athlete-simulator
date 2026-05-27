# skipper.py

from .base_character import Character
from power_system import PowerPhase

class Skipper(Character):
    """When anyone rolls a 1 for their main move, I go next in turn order."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roll == 1 and not self.finished:
            self.register_ability_use(game, play_by_play_lines, description="Skipper")
            if roller is self:
                play_by_play_lines.append(f"{self.name} ({self.piece}) rolled a 1 — will take another turn next!")
            else:
                play_by_play_lines.append(f"{self.name} ({self.piece}) will go next because {roller.name} rolled a 1!")

            # Queue Skipper to go after the current player's turn completes.
            # The queued_turns loop in Game.run snapshots before iterating, so a
            # chained self-trigger (Skipper rolls another 1 on the queued turn)
            # is picked up on the next outer-loop iteration — bounded by the
            # turn-event watchdog, no infinite loop risk.
            if not hasattr(game, 'queued_turns'):
                game.queued_turns = []
            game.queued_turns.append(self)