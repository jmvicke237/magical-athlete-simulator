# cheatah.py

import random
from .base_character import Character
from power_system import PowerPhase

class Cheatah(Character):
    """Instead of rolling for my main move, I secretly set my die to any number 1-6.
    The player to my right guesses; either way I move the chosen value, but on
    a correct guess I'm also tripped on my next turn (caught cheating).
    Doesn't count as a roll, so power triggers (Inchworm, StinkEye, Skipper,
    Weremouth, SilverSpoon) don't fire and roll modifications (Coach, Gunk,
    Blimp) don't apply.

    Variant (Game.cheatah_alt_mode == True): same rules as default,
    but both Cheatah and the guesser pick from the restricted range
    4-6 instead of 1-6. Higher floor on movement, but the guess space
    shrinks to three options (1-in-3 correct vs 1-in-6 baseline)."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        # If Cheatah was tripped coming into this turn, base.take_turn
        # already cleared self.tripped and set skip_main_move=True before
        # PRE_ROLL fired. Skip the cheat — no die-setting, no movement —
        # otherwise a correct-guess trip from last turn does nothing.
        if self.skip_main_move:
            return

        # Pick range: default 1-6; alt mode restricts both Cheatah's
        # chosen value and the guesser's guess to 4-6 (shorter wrong-guess
        # tail, smaller guess space → higher hit rate).
        alt_mode = getattr(game, "cheatah_alt_mode", False)
        low, high = (4, 6) if alt_mode else (1, 6)

        chosen = random.randint(low, high)
        guesser = self._find_right_neighbor(game)

        # Suppress the normal roll pipeline (rerolls, triggers, modifications, MOVEMENT)
        # — the chosen value is not a "roll" per spec.
        self.skip_main_move = True
        self.register_ability_use(game, play_by_play_lines, description="Cheatah")

        range_tag = f" (alt mode, {low}-{high})" if alt_mode else ""

        if guesser is None:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) sets the die to {chosen}{range_tag} "
                f"(no neighbor to guess)."
            )
            self.move(game, play_by_play_lines, chosen)
            return

        guess = random.randint(low, high)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) sets the die to {chosen}{range_tag}; "
            f"{guesser.name} ({guesser.piece}) guesses {guess}."
        )

        if guess == chosen:
            # Correct guess: Cheatah is caught cheating. Still moves the
            # chosen value this turn, but gets tripped (skips next main
            # move). self.tripped is set AFTER self.move so the trip
            # doesn't bleed into anything mid-move.
            play_by_play_lines.append(
                f"  Correct guess — {self.name} ({self.piece}) is caught! "
                f"Moves {chosen} but trips next turn."
            )
            self.move(game, play_by_play_lines, chosen)
            self.tripped = True
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
