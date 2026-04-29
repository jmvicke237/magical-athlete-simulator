# cheatah.py

import random
from .base_character import Character
from power_system import PowerPhase

class Cheatah(Character):
    """Instead of rolling for my main move, I secretly set my die to any number 1-6.
    The player to my right guesses; if they guess correctly, I don't move.
    Doesn't count as a roll, so power triggers (Inchworm, StinkEye, Skipper,
    Weremouth, SilverSpoon) don't fire and roll modifications (Coach, Gunk,
    Blimp) don't apply."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return

        # Cheatah picks; neighbor (next active player in turn order) guesses.
        chosen = random.randint(1, 6)
        guesser = self._find_right_neighbor(game)

        # Suppress the normal roll pipeline (rerolls, triggers, modifications, MOVEMENT)
        # — the chosen value is not a "roll" per spec.
        self.skip_main_move = True
        self.register_ability_use(game, play_by_play_lines, description="Cheatah")

        if guesser is None:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) sets the die to {chosen} (no neighbor to guess)."
            )
            self.move(game, play_by_play_lines, chosen)
            return

        guess = random.randint(1, 6)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) sets the die to {chosen}; "
            f"{guesser.name} ({guesser.piece}) guesses {guess}."
        )

        if guess == chosen:
            play_by_play_lines.append(
                f"  Correct guess — {self.name} ({self.piece}) doesn't move."
            )
            return

        play_by_play_lines.append(
            f"  Wrong guess — {self.name} ({self.piece}) moves {chosen}."
        )
        self.move(game, play_by_play_lines, chosen)

    def _find_right_neighbor(self, game):
        """Next active player in turn order (clockwise from me)."""
        n = len(game.turn_order)
        if n <= 1:
            return None
        for i in range(1, n):
            idx = (game.current_player_index + i) % n
            candidate = game.players[game.turn_order[idx]]
            if (candidate is not self
                    and not candidate.finished
                    and candidate not in game.eliminated_players):
                return candidate
        return None
