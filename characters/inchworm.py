# inchworm.py

from .base_character import Character

class Inchworm(Character):
   def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        """If another player rolls a 1, they don't move, and Inchworm moves 1."""
        if roller != self and roll == 1 and not self.finished:
            play_by_play_lines.append(f"{self.name} ({self.piece}) moves 1 space because {roller.name} ({roller.piece}) rolled a 1.")
            self.move(game, play_by_play_lines, 1)
            self.register_ability_use(game, play_by_play_lines, description="Inchworm")
            roller.skip_main_move = True