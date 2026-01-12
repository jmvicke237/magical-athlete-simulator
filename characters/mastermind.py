# mastermind.py

from .base_character import Character

class Mastermind(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.prediction = None  # Who the Mastermind predicts will win
        self.has_made_prediction = False
        self.bronze_chips = 0

    def make_prediction(self, game, play_by_play_lines):
        """Predicts the winner at the start of the game."""
        if not self.has_made_prediction:
            # For now, let's just predict the 2nd player will win, replace with the actual AI strategy later
            self.prediction = game.players[1]
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) predicts that {self.prediction.name} ({self.prediction.piece}) will win!"
            )
            self.has_made_prediction = True
            self.register_ability_use(game, play_by_play_lines, description="Mastermind")

    def check_prediction(self, game, play_by_play_lines):
        """Checks if the prediction is correct when the game ends."""
        if self.has_made_prediction and len(game.finished_players) > 0 and game.finished_players[0] == self.prediction:
            self.bronze_chips += 4
            play_by_play_lines.append(
                f"{self.name} ({self.piece})'s prediction was correct! They receive 4 bronze chips, ending the race early."
            )
            return True
        else:
            if len(game.finished_players) > 0:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece})'s prediction was INCORRECT! The winner was actually {game.finished_players[0].name} ({game.finished_players[0].piece})."
                )
            return False #Tell everyone that it was not True, so the loop can keep on going.