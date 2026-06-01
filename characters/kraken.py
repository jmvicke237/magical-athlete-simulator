# kraken.py

from .base_character import Character
from power_system import PowerPhase


class Kraken(Character):
    """Once per race, at the start of my turn, I can warp all other racers
    to my space and trip them.

    Simulator policy: "I can" is player choice. The sim fires the ability
    when another active racer is within `LATE_GAME_THRESHOLD` spaces of
    winning — late-game catch-up timing. Firing too early wastes the
    once-per-race effect on a field that hasn't spread out; this defers
    it until the field has actually pulled away.

    Finished and eliminated racers are not affected.

    Null interaction: pre_move_action is suppressed by the standard
    is_power_suppressed_for gate when Kraken is ahead of an active Null,
    so the warp doesn't fire (and the once-per-race usage isn't burned).
    """

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    # Trigger when any other racer is within this many spaces of winning.
    LATE_GAME_THRESHOLD = 6

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self._used = False

    def pre_move_action(self, game, play_by_play_lines):
        if self._used:
            return
        if self.finished or self in game.eliminated_players:
            return

        threshold = game.board.length - self.LATE_GAME_THRESHOLD
        active_others = [
            p for p in game.players
            if p is not self
            and not p.finished
            and p not in game.eliminated_players
        ]
        if not any(p.position >= threshold for p in active_others):
            return

        play_by_play_lines.append(
            f"{self.name} ({self.piece}) unleashes the Kraken — warping all "
            f"racers to space {self.position} and tripping them!"
        )
        self._used = True
        self.register_ability_use(game, play_by_play_lines, description="Kraken")
        for p in active_others:
            p.jump(game, self.position, play_by_play_lines)
            # Trip after warping. The trip flag affects the racer's NEXT main
            # move (per base.take_turn). Skip racers who got finished or
            # eliminated by the jump itself (e.g., landing on an elim space).
            if p.finished or p in game.eliminated_players:
                continue
            if not p.tripped:
                p.trip(game, play_by_play_lines)
                play_by_play_lines.append(
                    f"  {p.name} ({p.piece}) is tripped."
                )
