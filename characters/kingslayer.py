# kingslayer.py

import random
from .base_character import Character
from power_system import PowerPhase

class Kingslayer(Character):
    """Before my main move, I trip the racer in the lead. If tied, choose randomly.
    Never targets self."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if self.finished:
            return

        active = [p for p in game.players if not p.finished]
        if not active:
            return

        max_pos = max(p.position for p in active)
        # Only target non-self leaders — if Kingslayer is alone in the lead, do nothing
        leaders = [p for p in active if p.position == max_pos and p is not self]
        if not leaders:
            return

        target = random.choice(leaders)
        target.trip(game, play_by_play_lines)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) tripped lead racer {target.name} ({target.piece}) at position {target.position}."
        )
        self.register_ability_use(game, play_by_play_lines, description="Kingslayer")
