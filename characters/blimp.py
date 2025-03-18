# characters/blimp.py

from .base_character import Character

class Blimp(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def modify_roll(self, game, play_by_play_lines, roll):
        """Modifies the Blimp's roll based on its position."""

        if self.turn_start_position < game.board.corner_position:  # Directly access corner_position
            modified_roll = roll + 2
            play_by_play_lines.append(f"{self.name} ({self.piece}) gets +2 to their roll (before corner). Roll: {roll} -> {modified_roll}")
        else:
            modified_roll = max(1, roll - 1)
            play_by_play_lines.append(f"{self.name} ({self.piece}) gets -1 to their roll (on or after corner). Roll: {roll} -> {modified_roll}")
        
        for other_player in game.players:
            if hasattr(other_player, "modify_other_roll"):
                modified_roll = other_player.modify_other_roll(self, game, play_by_play_lines, modified_roll)
        
        game.trigger_scoocher(play_by_play_lines)

        return modified_roll