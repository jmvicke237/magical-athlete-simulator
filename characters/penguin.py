# penguin.py

from .base_character import Character
from power_system import PowerPhase


class Penguin(Character):
    """Whenever a racer passes me, I trip. When I'm tripped, double my roll
    for my main move instead of skipping it.

    Two-phase mechanic:
      - Trigger: on_being_passed sets self.tripped = True. Trip flag is
        gated by Antimag suppression so racers ahead of Antimag don't
        proc Penguin's trip.
      - Recovery: take_turn override clears the trip BEFORE base sees it
        (so base.take_turn doesn't set skip_main_move) and stashes a flag
        for pre_move_action. The pre_move_action (PRE_ROLL phase) reads
        the flag and bumps main_move_multiplier *= 2 — the rest of the
        roll pipeline (ROLL_MODIFICATION, Antimag penalty, etc.) still
        applies on top of the doubled value.

    Antimag interaction: if Penguin is strictly ahead of an active Antimag,
    powers are suppressed. on_being_passed is gated by suppression. The
    take_turn override defers to base behavior (normal skip-main-move)
    when suppressed, so Penguin can't free-recover out of suppression.
    """

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        # Carries from take_turn (decided to recover via doubling) into
        # pre_move_action (where the x2 is applied). base.take_turn resets
        # main_move_multiplier at the top of every turn, so we have to set
        # it during PRE_ROLL, not before super().
        self._double_next_main_move = False

    def on_being_passed(self, passing_player, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        if self.tripped:
            return
        self.trip(game, play_by_play_lines)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) trips after being passed by "
            f"{passing_player.name} ({passing_player.piece})."
        )
        self.register_ability_use(game, play_by_play_lines, description="Penguin")

    def take_turn(self, game, play_by_play_lines):
        # Recovery: clear the trip BEFORE base sees it (so base doesn't set
        # skip_main_move) and stash a flag for pre_move_action.
        if self.tripped and not game.is_power_suppressed_for(self):
            self.tripped = False
            self._double_next_main_move = True
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) was tripped — Penguin moves "
                f"double their roll instead of skipping."
            )
        super().take_turn(game, play_by_play_lines)

    def pre_move_action(self, game, play_by_play_lines):
        # Apply the x2 multiplier on a recovery turn.
        if self._double_next_main_move:
            self._double_next_main_move = False
            self.main_move_multiplier *= 2
