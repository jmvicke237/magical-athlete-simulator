# genius.py

from .base_character import Character
import random

class Genius(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.lucky_number = 6
        self.guessed_right = False
        self.my_turn_order = -1

    def pre_move_action(self, game, play_by_play_lines):
        self.lucky_number = random.randint(1, 6)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) predicts they will roll a {self.lucky_number}"
        )

    def main_roll(self, game, play_by_play_lines):
        roll = super().main_roll(game, play_by_play_lines)  # Use the base Character's roll

        if roll == 6:
            for player in game.players:
                if player.piece == "Lackey":
                    play_by_play_lines.append(
                        f"{player.name} ({player.piece}) moved 2 because {self.name} rolled a 6!"
                    )
                    player.move(game, play_by_play_lines, 2)
                    game.trigger_scoocher(play_by_play_lines) #Lackey scoocher trigger
        
        if roll == self.lucky_number:
            self.guessed_right = True
        
        return roll

    def post_move_ability(self, game, play_by_play_lines):
        if self.guessed_right:
            self.guessed_right = False
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) guessed correctly and gets another turn!"
            )
            self.reverting = True
            #Revert turn and trigger more actions.
            game.current_player_index = (game.current_player_index - 1) % len(game.turn_order)
            
            game.trigger_scoocher(play_by_play_lines)