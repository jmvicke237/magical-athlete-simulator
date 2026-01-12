# mouth.py

from .base_character import Character

class MOUTH(Character): #I fixed the class to be correct.
    def move(self, game, play_by_play_lines, spaces):
        super().move(game, play_by_play_lines, spaces)
        self._check_and_eliminate(game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        super().jump(game, position, play_by_play_lines)
        self._check_and_eliminate(game, play_by_play_lines)

    def _check_and_eliminate(self, game, play_by_play_lines):
        """If the MOUTH moves to a space with exactly one other player, eliminate that player."""
        space_mates = self.check_for_share_space(game)
        if len(space_mates) == 1:
            eliminated_player = space_mates[0]
            game.eliminate_player(eliminated_player, play_by_play_lines)
            self.register_ability_use(game, play_by_play_lines, description="MOUTH")