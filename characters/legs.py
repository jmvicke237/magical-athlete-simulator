# characters/legs.py

from .base_character import Character

class Legs(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def main_roll(self, game, play_by_play_lines):
        """Legs always rolls a 5 (for their main move)."""
        roll = 5
        play_by_play_lines.append(f"{self.name} ({self.piece}) effectively rolled a 5 (always moves 5).")
        self.last_roll = roll  # Still store the roll for consistency
        game.trigger_scoocher(play_by_play_lines)
        return roll