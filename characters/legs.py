# characters/legs.py

from .base_character import Character

class Legs(Character):

    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def main_roll(self, game, play_by_play_lines):
        """Legs always rolls a 5 (for their main move)."""
        # Abilities-off endgame: roll a plain d6 like everyone else.
        if getattr(game, 'abilities_disabled', False):
            return Character.main_roll(self, game, play_by_play_lines)
        roll = 5
        play_by_play_lines.append(f"{self.name} ({self.piece}) effectively rolled a 5 (always moves 5).")
        self.last_roll = roll  # Still store the roll for consistency
        self.register_ability_use(game, play_by_play_lines, description="Legs")
        return roll