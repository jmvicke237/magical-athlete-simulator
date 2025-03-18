# characters/centaur.py

from .base_character import Character

class Centaur(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def move(self, game, play_by_play_lines, spaces):
        # Get the list of players *ahead* of the Centaur before the move
        racers_in_front_before = self._get_racers_in_front(game)

        super().move(game, play_by_play_lines, spaces)

        # No need to get racers_behind *after*.  We can directly
        # find newly passed players by comparing positions.

        for player in racers_in_front_before:
            if self.position > player.position and not player.finished:  # Now behind
                play_by_play_lines.append(f"{self.name} ({self.piece}) passed {player.name} ({player.piece}), moving them back 2 spaces.")
                player.move(game, play_by_play_lines, -2)
                game.trigger_scoocher(play_by_play_lines)

    def _get_racers_in_front(self, game):
        """Helper function to get a list of players ahead of the Centaur."""
        in_front = []
        for other_player in game.players:
            if other_player != self and self.position < other_player.position and not other_player.finished:
                in_front.append(other_player)
        return in_front