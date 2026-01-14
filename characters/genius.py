# genius.py

from .base_character import Character
from power_system import PowerPhase
import random

class Genius(Character):
    """I can predict what number I'll roll for my main move. If I'm right, I take another turn after this one."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}

    def __init__(self, name, piece):
        super().__init__(name, piece)
        # For AI, randomly pick a number to predict each turn
        self.lucky_number = random.randint(1, 6)
        self.guessed_right = False
        self.my_turn_order = -1

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        """Check if Genius predicted their roll correctly."""
        if roller == self:
            # Make a new prediction for this roll
            self.lucky_number = random.randint(1, 6)
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) predicts they will roll a {self.lucky_number}..."
            )

            if roll == self.lucky_number:
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
    
