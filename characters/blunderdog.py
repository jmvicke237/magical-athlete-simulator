# blunderdog.py

from .base_character import Character
from power_system import PowerPhase

class Blunderdog(Character):
    """When I'm in last place at the start of my turn, my main move is tripled.
    Otherwise it's reversed. The multiplier applies to the final roll AFTER any
    Coach/Gunk/etc. modifications (consistent with how StinkEye stacks)."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        if self.skip_main_move:
            return  # tripped, etc.

        others = [
            p for p in game.players
            if p is not self and p not in game.eliminated_players
        ]
        if not others:
            return

        min_other = min(p.position for p in others)
        if self.position <= min_other:
            self.main_move_multiplier *= 3
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) is in last place — main move will be tripled."
            )
        else:
            self.main_move_multiplier *= -1
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) is not in last place — main move will be reversed."
            )
        self.register_ability_use(game, play_by_play_lines, description="Blunderdog")
