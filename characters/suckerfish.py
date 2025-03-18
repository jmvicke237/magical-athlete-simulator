# suckerfish.py

from .base_character import Character

class Suckerfish(Character):
    def move_with_another(self, moved_player, spaces, game, play_by_play_lines):
        """Move with another racer when they start moving from my space."""
        if moved_player != self and moved_player.previous_position == self.position and not self.finished:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moves with {moved_player.name} ({moved_player.piece}) from Space {self.position} to Space {moved_player.position}."
            )
            self.move(game, play_by_play_lines, spaces)
            game.trigger_scoocher(play_by_play_lines)
            