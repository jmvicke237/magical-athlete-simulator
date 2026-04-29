# blackhole.py

from .base_character import Character
from power_system import PowerPhase

class BlackHole(Character):
    """Once per race, before my main move, if another active racer is within
    6 spaces of winning (position >= board.length - 6), I warp all other
    active racers to my space. Finished and eliminated racers are not warped."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self._used = False

    def pre_move_action(self, game, play_by_play_lines):
        if self._used:
            return
        if self.finished or self in game.eliminated_players:
            return

        threshold = game.board.length - 6  # within 6 of winning
        active_others = [
            p for p in game.players
            if p is not self
            and not p.finished
            and p not in game.eliminated_players
        ]
        if not any(p.position >= threshold for p in active_others):
            return

        play_by_play_lines.append(
            f"{self.name} ({self.piece}) opens a black hole — warping all racers to space {self.position}!"
        )
        self._used = True
        self.register_ability_use(game, play_by_play_lines, description="BlackHole")
        for p in active_others:
            p.jump(game, self.position, play_by_play_lines)
