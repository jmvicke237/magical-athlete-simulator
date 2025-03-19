# magician.py

from .base_character import Character
import random

class Magician(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def reroll_main_roll(self, roller, game, play_by_play_lines, roll):
        """The Magician may reroll up to 2 times per turn, then re-check for a new target."""
        mouth_position = -1
        reroll_count = 0 #number of rerolls
        spaces_to_finish = game.board.length - self.position
        for player in game.players:
            if player.piece == "MOUTH":
                mouth_position = player.position
        if reroll_count < 2: #The magician can only reroll it two times.
            reroll_count += 1 #Count for that reroll.
            # Check if MOUTH is in the game and block the action if the result would make the Magician land in same spot as mouth:
            if roller == self and roll <= 3 or (spaces_to_finish <= 6 and roll < spaces_to_finish) or (self.position + roll == mouth_position): #should only reroll in those cases.
                play_by_play_lines.append(f"{self.name} ({self.piece}) chooses to reroll")
                roll = self.main_roll(game, play_by_play_lines) #Make a new roll and trigger new events
                self.register_ability_use(game, play_by_play_lines, description="Magician")
            #Reset that counter
        return roll #The result of the function returns