# characters/dicemonger.py

from .base_character import Character
import random

class Dicemonger(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def reroll_main_roll(self, other_player, game, play_by_play_lines, roll):
        """Allows the other player to reroll, based on Dicemonger rules."""
        mouth_position = -1
        for player in game.players:
            if player.piece == "MOUTH":
                mouth_position = player.position
        spaces_to_finish = game.board.length - other_player.position
        if roll <= 3 or (spaces_to_finish <= 6 and roll < spaces_to_finish) or (self.position + roll == mouth_position):
            play_by_play_lines.append(f"{other_player.name} ({other_player.piece}) chooses to reroll by using {self.name} ({self.piece}).")
            new_roll = other_player.main_roll(game, play_by_play_lines)
            if other_player.name != self.name:
                self.move(game, play_by_play_lines, 1)
                play_by_play_lines.append(f"{self.name} (Dicemonger) moves 1 because another player rerolled.") # CORRECTED
            self.register_ability_use(game, play_by_play_lines, description="Dicemonger")
            return new_roll

        return roll  # Return original roll if no reroll
    
    
    