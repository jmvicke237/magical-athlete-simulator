# characters/centaur.py

from .base_character import Character

class Centaur(Character):
    """When I pass a racer, they move -2."""


    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def move(self, game, play_by_play_lines, spaces):
        # Record position before moving
        start_position = self.position

        # Execute the move
        super().move(game, play_by_play_lines, spaces)

        # Use centralized passing detection
        passed_racers = self.detect_passes(game, start_position, self.position)

        # Apply Centaur's ability to each passed racer
        for player in passed_racers:
            if not player.finished:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) passed {player.name} ({player.piece}), moving them back 2 spaces."
                )
                player.move(game, play_by_play_lines, -2)
                self.register_ability_use(game, play_by_play_lines, description="Centaur")