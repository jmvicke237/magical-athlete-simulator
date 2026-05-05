# penguin.py

from .base_character import Character
from power_system import PowerPhase


class Penguin(Character):
    """Two switchable rule sets, controlled by Game.penguin_alt_mode:

    Default mode (penguin_alt_mode == False):
      "When a racer passes me, I trip. I don't skip my main move when I'm
      tripped: I move N (Game.penguin_recovery_move, default 3) and recover."

      - on_being_passed sets self.tripped = True (gated by Antimag).
      - take_turn intercepts a tripped turn before base.take_turn would
        skip the main move and runs a hand-rolled recovery turn that
        moves a fixed N spaces, bypassing the entire roll pipeline
        (no roll, no DIE_ROLL_TRIGGER, no ROLL_MODIFICATION, no
        multiplier, no Antimag main-move penalty).

    Alt mode (penguin_alt_mode == True):
      "When I stop on a racer or a racer stops on me, I trip. I don't skip
      my main move when I'm tripped: I move double my roll instead, then
      recover."

      - Trigger fires only on movement-landing events, not at arbitrary
        turn boundaries (an earlier POST_TURN-based version mis-fired
        on turn 1 when racers were still tied at the start space):
          * on_another_player_move / on_another_player_jump: another
            racer just moved/warped — if they landed on Penguin's space,
            Penguin trips.
          * move / jump overrides: after Penguin's own move/jump, if
            position changed AND Penguin is now sharing a space with at
            least one racer, Penguin trips. The position-changed guard
            keeps a no-op move (move(0), Stickler-blocked move, jump to
            same space) from re-checking and triggering on already-shared
            starting spaces.
      - take_turn clears the trip BEFORE base sees it, stashes a flag,
        and lets base.take_turn run normally. pre_move_action (PRE_ROLL
        phase) reads the flag and bumps main_move_multiplier *= 2 — the
        rest of the roll pipeline (ROLL_MODIFICATION, Antimag penalty,
        etc.) still applies on top of the doubled value.

    Antimag interaction (both modes): if Penguin is strictly ahead of an
    active Antimag, powers are suppressed. Triggers (on_being_passed in
    default, post_turn_actions in alt) are gated by suppression. The
    take_turn override defers to base behavior (normal skip-main-move)
    when suppressed, so Penguin can't free-recover out of suppression.
    """

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    DEFAULT_RECOVERY_MOVE = 3

    def __init__(self, name, piece):
        super().__init__(name, piece)
        # Alt-mode flag: carries from take_turn (decided to recover via
        # doubling) into pre_move_action (where the x2 is applied).
        # base.take_turn resets main_move_multiplier at the top of every
        # turn, so we have to set it during PRE_ROLL, not before super().
        self._double_next_main_move = False

    # ------------------------------------------------------------------
    # Triggers
    # ------------------------------------------------------------------

    def on_being_passed(self, passing_player, game, play_by_play_lines):
        # Default mode only — alt mode uses POST_TURN share-space detection.
        if getattr(game, "penguin_alt_mode", False):
            return
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

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        # Alt mode only — case "a racer stops on me": fires from base.move
        # after the moved player's segment lands. If they ended on
        # Penguin's space, trip. The previous_position guard skips no-op
        # moves (e.g., move clamped to current position) so we only
        # trigger on a real arrival event, not a passive share.
        if not getattr(game, "penguin_alt_mode", False):
            return
        if moved_player.position != self.position:
            return
        if moved_player.position == getattr(moved_player, "previous_position", moved_player.position):
            return
        self._maybe_alt_trip(
            f"{moved_player.name} ({moved_player.piece}) stopped on me",
            game,
            play_by_play_lines,
        )

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        # Alt mode only — case "a racer warps onto me": same logic as
        # on_another_player_move but for jumps (Mole, Buddy, portals,
        # MagicalAthlete spells, swap_positions). Per the warp rule, a
        # warp does trigger a "stop" event (just not a "pass"), so
        # share-space at the destination of a real warp does trip Penguin.
        # The previous_position guard skips no-op jumps (jump to current
        # position) — those aren't real arrival events.
        if not getattr(game, "penguin_alt_mode", False):
            return
        if jumped_player.position != self.position:
            return
        if jumped_player.position == getattr(jumped_player, "previous_position", jumped_player.position):
            return
        self._maybe_alt_trip(
            f"{jumped_player.name} ({jumped_player.piece}) warped onto me",
            game,
            play_by_play_lines,
        )

    def move(self, game, play_by_play_lines, spaces):
        # Alt mode only — case "I stop on a racer": override base.move
        # to add a post-move share-space check, gated on actual position
        # change so move(0) / Stickler-blocked moves don't re-fire on
        # already-shared starting spaces.
        pre = self.position
        super().move(game, play_by_play_lines, spaces)
        if not getattr(game, "penguin_alt_mode", False):
            return
        if self.position == pre:
            return
        self._check_self_landed_on_racer(game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        # Alt mode only — case "I warp onto a racer".
        pre = self.position
        super().jump(game, position, play_by_play_lines)
        if not getattr(game, "penguin_alt_mode", False):
            return
        if self.position == pre:
            return
        self._check_self_landed_on_racer(game, play_by_play_lines)

    def _check_self_landed_on_racer(self, game, play_by_play_lines):
        space_mates = self.check_for_share_space(game)
        if not space_mates:
            return
        names = ", ".join(f"{p.name} ({p.piece})" for p in space_mates)
        self._maybe_alt_trip(f"stopped on {names}", game, play_by_play_lines)

    def _maybe_alt_trip(self, reason, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        if self.tripped:
            return
        self.trip(game, play_by_play_lines)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) — {reason} — trips!"
        )
        self.register_ability_use(game, play_by_play_lines, description="Penguin")

    # ------------------------------------------------------------------
    # Turn handling
    # ------------------------------------------------------------------

    def take_turn(self, game, play_by_play_lines):
        if getattr(game, "penguin_alt_mode", False):
            self._take_turn_alt(game, play_by_play_lines)
        else:
            self._take_turn_default(game, play_by_play_lines)

    def _take_turn_default(self, game, play_by_play_lines):
        recovery_spaces = getattr(game, "penguin_recovery_move", self.DEFAULT_RECOVERY_MOVE)
        if (self.tripped
                and recovery_spaces > 0
                and not game.is_power_suppressed_for(self)):
            self._do_recovery_turn(game, play_by_play_lines, recovery_spaces)
            return
        super().take_turn(game, play_by_play_lines)

    def _take_turn_alt(self, game, play_by_play_lines):
        # Alt-mode recovery: clear the trip BEFORE base sees it (so base
        # doesn't set skip_main_move) and stash a flag for pre_move_action.
        if self.tripped and not game.is_power_suppressed_for(self):
            self.tripped = False
            self._double_next_main_move = True
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) was tripped — Penguin moves "
                f"double their roll instead and recovers."
            )
        super().take_turn(game, play_by_play_lines)

    def pre_move_action(self, game, play_by_play_lines):
        # Alt-mode-only: apply the x2 multiplier on a recovery turn.
        if self._double_next_main_move:
            self._double_next_main_move = False
            self.main_move_multiplier *= 2

    def _do_recovery_turn(self, game, play_by_play_lines, spaces):
        """Default-mode recovery: hand-rolled phase pipeline that runs
        the same non-roll phases as a normal turn but replaces the main
        move with a flat N-space move (no roll, no roll modifiers)."""
        self.turn_start_position = self.position
        self.last_roll = -1
        self.main_move_multiplier = 1
        self.tripped = False
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) was tripped — Penguin moves {spaces} and recovers."
        )

        game.resolve_phase(PowerPhase.PRE_ROLL, self, play_by_play_lines)

        self.move(game, play_by_play_lines, spaces)

        game.resolve_phase(PowerPhase.POST_MOVEMENT, self, play_by_play_lines)

        if not game.is_power_suppressed_for(self):
            self.post_move_ability(game, play_by_play_lines)

        game.resolve_phase(PowerPhase.OTHER_REACTIONS, self, play_by_play_lines)
        game.resolve_phase(PowerPhase.POST_TURN, self, play_by_play_lines)

        game.clear_state_history()
