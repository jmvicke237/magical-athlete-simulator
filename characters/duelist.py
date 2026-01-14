# characters/duelist.py

from .base_character import Character
from power_system import PowerPhase

class Duelist(Character):
    """Whenever a racer shares my space, I can shout DUEL! We roll dice and whoever rolls highest moves 2.

    This triggers after ANY player's turn (not just Duelist's turn) via the POST_TURN phase.
    If Duelist shares a space with anyone at the end of any turn, a duel is initiated.
    """

    POWER_PHASES = {PowerPhase.POST_TURN}
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def post_turn_actions(self, game, other_player, play_by_play_lines):
        """Check if Duelist shares a space with anyone and initiate duels.

        This is called after EVERY player's turn (via POST_TURN phase).
        If duels cause infinite loops, the loop detection in move() will
        prevent the move and we'll continue to the next player's turn.
        """
        if not self.finished:
            space_mates = self.check_for_share_space(game)
            if space_mates:
                play_by_play_lines.append(f"{self.name} ({self.piece}) initiates a duel!")
                for opponent in space_mates:
                    self.duel(opponent, game, play_by_play_lines)

    def duel(self, other_player, game, play_by_play_lines):
        """Conducts a duel with another player."""

        play_by_play_lines.append(f"{self.name} ({self.piece}) duels {other_player.name} ({other_player.piece})!")

        my_roll = self.main_roll(game, play_by_play_lines)
        other_roll = other_player.main_roll(game, play_by_play_lines)

        play_by_play_lines.append(f"{self.name} ({self.piece}) rolled {my_roll}, {other_player.name} ({other_player.piece}) rolled {other_roll}.")

        if my_roll >= other_roll:
            play_by_play_lines.append(f"{self.name} ({self.piece}) wins the duel!")
            self.move(game, play_by_play_lines, 2)
            self.register_ability_use(game, play_by_play_lines, description="Duelist")
        else:
            play_by_play_lines.append(f"{other_player.name} ({other_player.piece}) wins the duel!")
            other_player.move(game, play_by_play_lines, 2)
            self.register_ability_use(game, play_by_play_lines, description="Duelist")