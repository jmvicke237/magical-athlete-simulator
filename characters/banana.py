# characters/banana.py

from .base_character import Character

class Banana(Character):
    """When a racer passes me, they trip."""


    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def on_being_passed(self, passing_player, game, play_by_play_lines):
        """Banana's ability: When a racer passes me, they trip."""
        if not passing_player.tripped:
            passing_player.trip(game, play_by_play_lines)
            play_by_play_lines.append(
                f"{passing_player.name} ({passing_player.piece}) tripped because they passed {self.name} ({self.piece})!"
            )
            self.register_ability_use(game, play_by_play_lines, description="Banana")