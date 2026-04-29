# caboose.py

import random
from .base_character import Character
from power_system import PowerPhase

class Caboose(Character):
    """Before my main move: if I'm in last, swap with the lead racer.
    If I'm in the lead, swap with the last-place racer. Random tie-break at either end."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if self.finished:
            return

        active = [p for p in game.players if not p.finished]
        if len(active) < 2:
            return

        min_pos = min(p.position for p in active)
        max_pos = max(p.position for p in active)
        if min_pos == max_pos:
            return  # everyone tied — swap is meaningless

        if self.position == min_pos:
            target_pool = [p for p in active if p.position == max_pos]
            role = "lead"
        elif self.position == max_pos:
            target_pool = [p for p in active if p.position == min_pos]
            role = "last-place"
        else:
            return

        target = random.choice(target_pool)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) swaps with {role} racer {target.name} ({target.piece})."
        )
        self.swap_positions(target, game, play_by_play_lines)
        self.register_ability_use(game, play_by_play_lines, description="Caboose")
