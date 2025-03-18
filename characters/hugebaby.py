# hugebaby.py

from .base_character import Character

class HugeBaby(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        self._check_shared_space(game, play_by_play_lines)

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        self._check_shared_space(game, play_by_play_lines)

    def move(self, game, play_by_play_lines, spaces):
        super().move(game, play_by_play_lines, spaces)
        self._check_shared_space(game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        super().jump(game, position, play_by_play_lines)
        self._check_shared_space(game, play_by_play_lines)
    
    def _check_shared_space(self, game, play_by_play_lines):
        """If any player (including Huge Baby) is on another player's space (other than the start), the other player gets pushed back."""
        if self.position > 0:
            for other_player in game.players:
                 if other_player != self and other_player.position == self.position:
                    other_player.move(game, play_by_play_lines, -1)
                    play_by_play_lines.append(f"{other_player.name} ({other_player.piece}) was pushed back by {self.name} ({self.piece})!")
                    # Don't trigger Scoocher if the pushed player is Scoocher
                    if other_player.piece != "Scoocher":
                        game.trigger_scoocher(play_by_play_lines)
