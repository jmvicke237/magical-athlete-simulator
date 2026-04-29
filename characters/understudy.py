# understudy.py

import random
from .base_character import Character
from power_system import PowerPhase

class Understudy(Character):
    """When other racers roll for their main move, I roll too. If we match,
    I move that amount.

    The understudy roll is a separate d6 — it doesn't go through main_roll, so
    it doesn't fire other characters' DIE_ROLL_TRIGGERs (Inchworm on a 1,
    StinkEye on a 3). PartyPooper's "any d6 of 6 forces a reroll" still applies
    via the shared _trigger_party_pooper helper.
    """

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}
    EDITION = "v2"

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roller is self:
            return
        if self.finished or self in game.eliminated_players:
            return

        my_roll = random.randint(1, 6)
        while my_roll == 6 and self._trigger_party_pooper(game, play_by_play_lines):
            my_roll = random.randint(1, 6)

        if my_roll == roll:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) understudy-rolls a {my_roll}, "
                f"matching {roller.name} ({roller.piece}) — moves {my_roll}!"
            )
            self.move(game, play_by_play_lines, my_roll)
            self.register_ability_use(game, play_by_play_lines, description="Understudy")
        else:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) understudy-rolls a {my_roll} "
                f"(no match with {roller.name}'s {roll})"
            )
