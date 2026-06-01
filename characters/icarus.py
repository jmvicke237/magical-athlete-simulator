# icarus.py

from .base_character import Character
from power_system import PowerPhase


class Icarus(Character):
    """I get +3 to my main move. If I roll a 6 for my main move, I'm eliminated.

    Flat +3 modifier on every main move (via ROLL_MODIFICATION phase), with
    a deadly downside: rolling a 6 on the natural die (before any modifier)
    eliminates Icarus immediately. The +3 buff is suppressed when Icarus is
    strictly ahead of an active Null — standard power-suppression rules. The
    self-elimination on 6 is part of Icarus's power, so suppression skips
    that too: a powerless Icarus just moves normally with no bonus and no risk.
    """

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER, PowerPhase.ROLL_MODIFICATION}
    EDITION = "v2"

    BONUS = 3

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roller is not self:
            return
        if self.finished or self in game.eliminated_players:
            return
        if game.is_power_suppressed_for(self):
            return
        if roll == 6:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) flew too close to the sun — "
                f"rolled a 6 and is eliminated!"
            )
            self.skip_main_move = True
            self.last_roll = 0
            game.eliminate_player(self, play_by_play_lines)
            self.register_ability_use(
                game, play_by_play_lines, description="Icarus eliminated"
            )

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        if other_player is not self:
            return roll
        if self.finished or self in game.eliminated_players:
            return roll
        new_roll = roll + self.BONUS
        play_by_play_lines.append(
            f"  {self.name} ({self.piece}) soars +{self.BONUS}: {roll} -> {new_roll}"
        )
        self.register_ability_use(game, play_by_play_lines, description="Icarus")
        return new_roll
