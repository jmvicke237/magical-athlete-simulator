# sandbag.py

from .base_character import Character
from power_system import PowerPhase

class Sandbag(Character):
    """I get -1 to my main move. When the race ends, if I haven't passed the
    second corner (i.e., position <= corner_position), I get 3 points
    (3 bronze chips)."""

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}
    EDITION = "v2"

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        if (other_player is not self
                or self.finished
                or self in game.eliminated_players):
            return roll
        new_roll = roll - 1
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) gets -1 to their move. Roll: {roll} -> {new_roll}"
        )
        self.register_ability_use(game, play_by_play_lines, description="Sandbag")
        return new_roll

    def on_race_end(self, game, play_by_play_lines):
        # Eliminated Sandbag still gets the bonus if they're at/before the corner —
        # the spec says "I haven't passed the second corner" (state-based, not behavior-based).
        if self.position <= game.board.corner_position:
            self.bronze_chips += 3
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) didn't pass the second corner — gets 3 bronze chips!"
            )
            self.register_ability_use(
                game, play_by_play_lines, description="Sandbag end-of-race bonus"
            )
