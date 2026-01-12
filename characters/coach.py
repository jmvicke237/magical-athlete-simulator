# characters/coach.py

from .base_character import Character

class Coach(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Coach adds +1 to the roll of any players sharing its space."""
        if self.finished == True:
            return roll
        
        if self.position == other_player.position:
            modified_roll = roll + 1
            play_by_play_lines.append(
                f"{other_player.name} ({other_player.piece}) gets +1 to their roll from {self.name} ({self.piece}). Roll: {roll} -> {modified_roll}"
            )
            self.register_ability_use(game, play_by_play_lines, description="Coach")
            return modified_roll
        return roll