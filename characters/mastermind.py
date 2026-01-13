# mastermind.py

from .base_character import Character

class Mastermind(Character):

    POWER_PHASES = set()
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
        # Only check if prediction was made and first place has finished
        if not self.has_made_prediction or len(game.finished_players) == 0:
            return False

        # If prediction is correct and we haven't already finished
        if game.finished_players[0] == self.prediction and not self.finished:
            # Mastermind finishes in 2nd place
            self.finished = True
            self.bronze_chips += 4
            game.finished_players.append(self)
            play_by_play_lines.append(
                f"{self.name} ({self.piece})'s prediction was correct! They finish in 2nd place and receive 4 bronze chips, ending the race early."
            )
            return True

        # If first place is decided and prediction was wrong, report it once
        elif game.finished_players[0] != self.prediction and not self.finished:
            play_by_play_lines.append(
                f"{self.name} ({self.piece})'s prediction was INCORRECT! The winner was actually {game.finished_players[0].name} ({game.finished_players[0].piece})."
            )
            return False

        return False