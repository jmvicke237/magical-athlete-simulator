# spoilsport.py

from .base_character import Character
from power_system import PowerPhase

class Spoilsport(Character):
    """Before my main move: if every other (non-eliminated) racer is N+ spaces
    ahead (default N=3, configurable via Game.spoilsport_threshold), the race
    is cancelled. I get 1 bronze chip (1 point). Gold and silver chips already
    awarded for 1st/2nd place are revoked — no one gets placement points."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return

        contenders = [
            p for p in game.players
            if p is not self and p not in game.eliminated_players
        ]
        if not contenders:
            return  # alone — nothing to cancel

        threshold = getattr(game, "spoilsport_threshold", 3)
        if not all((p.position - self.position) >= threshold for p in contenders):
            return

        play_by_play_lines.append(
            f"{self.name} ({self.piece}) calls it off — every other racer is {threshold}+ spaces ahead. "
            f"The race is cancelled!"
        )

        # Consolation point for Spoilsport
        self.bronze_chips += 1
        play_by_play_lines.append(
            f"  {self.name} ({self.piece}) gets 1 bronze chip (1 point)."
        )

        # Revoke gold/silver chips already awarded for placement
        for p in game.players:
            if p is self:
                continue
            if p.gold_chips > 0 or p.silver_chips > 0:
                play_by_play_lines.append(
                    f"  {p.name} ({p.piece}) loses {p.gold_chips} gold and {p.silver_chips} silver chip(s)."
                )
                p.gold_chips = 0
                p.silver_chips = 0

        # End the race — Game.should_game_end picks this up after the turn returns.
        game.race_cancelled = True
        # Skip my own main move (race is over)
        self.skip_main_move = True
        self.register_ability_use(game, play_by_play_lines, description="Spoilsport")
