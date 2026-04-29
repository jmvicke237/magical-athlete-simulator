# apprentice.py

from .base_character import Character
from power_system import PowerPhase

class Apprentice(Character):
    """When I roll the same number for my main move as the last racer, I get
    another turn. I can do this multiple times — but each chained bonus must
    roll the SAME initial number (the original last-racer roll), not the
    previous bonus turn's roll."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        # Once I match the last racer, this locks in to that value for chaining.
        # Reset to None when I roll a non-matching value.
        self._chain_target = None

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roller is not self:
            return
        if self.finished or self in game.eliminated_players:
            self._chain_target = None
            return

        # Determine target: chain target if currently chaining, else last racer's roll.
        if self._chain_target is not None:
            target = self._chain_target
            mode = f"chain target {target}"
        else:
            target = getattr(game, '_last_main_roll', None)
            mode = f"last racer's {target}" if target is not None else None

        if target is None:
            return  # No previous racer to compare against (start of race)

        if roll == target:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) rolled {roll} matching {mode} — gets another turn!"
            )
            self._chain_target = target  # lock in for further chaining
            self.register_ability_use(game, play_by_play_lines, description="Apprentice")
            if not hasattr(game, 'queued_turns'):
                game.queued_turns = []
            game.queued_turns.append(self)
        else:
            # Non-match — chain ends if we were in one
            if self._chain_target is not None:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) rolled {roll} (didn't match chain target {self._chain_target}) — chain ends."
                )
                self._chain_target = None
