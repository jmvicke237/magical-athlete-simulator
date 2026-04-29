# zipper.py

from .base_character import Character
from power_system import PowerPhase

class Zipper(Character):
    """Before my main move, I warp to the space behind the closest active
    racer ahead of me. Finished and eliminated racers are excluded — Zipper
    only chases racers still in the race. If no active racer is ahead — no warp."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return

        ahead = [
            p for p in game.players
            if p is not self
            and not p.finished
            and p not in game.eliminated_players
            and p.position > self.position
        ]
        if not ahead:
            return  # No active racer ahead — no warp

        closest = min(ahead, key=lambda p: p.position)
        target = closest.position - 1
        if target == self.position:
            return  # I'm already directly behind them

        play_by_play_lines.append(
            f"{self.name} ({self.piece}) zips to space {target} "
            f"(behind {closest.name} ({closest.piece}) at {closest.position})."
        )
        self.jump(game, target, play_by_play_lines)
        self.register_ability_use(game, play_by_play_lines, description="Zipper")
