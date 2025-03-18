# skipper.py

from .base_character import Character

class Skipper(Character):
    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roll == 1 and not self.finished:
            game.trigger_scoocher(play_by_play_lines)
            game.change_turn_order(self, play_by_play_lines)