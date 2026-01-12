# lovableloser.py

from .base_character import Character
from power_system import PowerPhase

class LoveableLoser(Character):
    """At the start of my turn, I get a bronze point chip if I'm alone in last place."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.bronze_chips = 0

    def pre_move_action(self, game, play_by_play_lines):
        """Gains a bronze chip if in last place (untied) at the start of the turn."""
        if self.is_last_place(game):
            self.bronze_chips += 1
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) is in last place and receives a bronze chip!"
            )
            self.register_ability_use(game, play_by_play_lines, description="LoveableLoser")

    def is_last_place(self, game):
        """Checks if the Loveable Loser is in last place (strictly behind all other racers)."""
        for player in game.players:
            if player != self and not player.finished and player not in game.eliminated_players and player.position <= self.position:
                return False
        return True