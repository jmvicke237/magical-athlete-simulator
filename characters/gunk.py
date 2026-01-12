# gunk.py

from .base_character import Character

class Gunk(Character):
    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Gunk reduces other players' rolls by 1."""
        if other_player != self:  # Don't modify Gunk's own roll
            modified_roll = max(0, roll - 1)  # Ensure roll is at least 1
            play_by_play_lines.append(
                f"{other_player.name} ({other_player.piece})'s roll was reduced by 1 due to {self.name} ({self.piece}). Roll: {roll} -> {modified_roll}"
            )
            self.register_ability_use(game, play_by_play_lines, description="Gunk")
            return modified_roll
        return roll