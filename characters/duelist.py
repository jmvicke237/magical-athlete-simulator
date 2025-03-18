# characters/duelist.py

from .base_character import Character

class Duelist(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def post_turn_actions(self, game, other_player, play_by_play_lines):
        """Duelist initiates a duel with any other player on the same space."""
        if not self.finished: #Don't do anything if finished
            space_mates = self.check_for_share_space(game)
            if space_mates:  # Only duel if there are other players
                play_by_play_lines.append(f"{self.name} ({self.piece}) initiates a duel!")
                for other_player in space_mates:
                    self.duel(other_player, game, play_by_play_lines)

    def duel(self, other_player, game, play_by_play_lines):
        """Conducts a duel with another player."""

        play_by_play_lines.append(f"{self.name} ({self.piece}) duels {other_player.name} ({other_player.piece})!")

        my_roll = self.main_roll(game, play_by_play_lines)
        other_roll = other_player.main_roll(game, play_by_play_lines)

        play_by_play_lines.append(f"{self.name} ({self.piece}) rolled {my_roll}, {other_player.name} ({other_player.piece}) rolled {other_roll}.")

        if my_roll >= other_roll:
            play_by_play_lines.append(f"{self.name} ({self.piece}) wins the duel!")
            self.move(game, play_by_play_lines, 2)
            game.trigger_scoocher(play_by_play_lines)
        else:
            play_by_play_lines.append(f"{other_player.name} ({other_player.piece}) wins the duel!")
            other_player.move(game, play_by_play_lines, 2)
            game.trigger_scoocher(play_by_play_lines)