# genius.py

from .base_character import Character
import random

class Genius(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.lucky_number = 6
        self.guessed_right = False
        self.my_turn_order = -1
    
    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        """When another racer rolls a 6 for their main move, Lackey moves 2 spaces before they move."""
        if roller == self and roll == self.lucky_number:
            self.guessed_right = True

    def post_move_ability(self, game, play_by_play_lines):
        if self.guessed_right:
            self.guessed_right = False
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) guessed correctly and gets another turn!"
            )
            self.reverting = True
            #Revert turn and trigger more actions.
            game.current_player_index = (game.current_player_index - 1) % len(game.turn_order)
            
            self.register_ability_use(game, play_by_play_lines, description="Genius")
    
