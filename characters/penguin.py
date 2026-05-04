# penguin.py

from .base_character import Character
from power_system import PowerPhase


class Penguin(Character):
    """When a racer passes me, I trip. I don't skip my main move when I'm
    tripped: I move 3 then recover.

    Implementation:
      - on_being_passed flips self.tripped = True (via Character.trip).
      - take_turn intercepts a tripped turn entirely. Instead of letting
        base.take_turn skip the main move (or going through the roll
        pipeline), it orchestrates a recovery turn: PRE_ROLL fires for
        parity with other tripped turns, then a fixed 3-space move is
        executed directly via self.move(), then POST_MOVEMENT,
        post_move_ability, OTHER_REACTIONS, and POST_TURN run.

    The recovery move bypasses main_roll entirely — no rerolls (Magician,
    Dicemonger), no DIE_ROLL_TRIGGER (Inchworm, Skipper), no
    ROLL_MODIFICATION (Gunk, Coach, Blimp), no main_move_multiplier
    (StinkEye, Blunderdog), and no Antimag main-move penalty. The "move 3"
    is a fixed effect, not a main-move roll, so nothing that targets a
    roll value applies.

    Antimag interaction: if Penguin is strictly ahead of an active Antimag,
    powers are suppressed. The on_being_passed trip is gated by base.move's
    suppression check (so the trip never sets); and the take_turn override
    defers to base behavior (normal skip-main-move) when suppressed, so
    Penguin can't free-recover out of suppression.
    """

    POWER_PHASES = set()
    EDITION = "v2"

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
        # Recovery move is configured per-game (default 3). 0 means the
        # toggle is "off" — Penguin falls back to base trip behavior
        # (skip the main move) on a tripped turn.
        recovery_spaces = getattr(game, "penguin_recovery_move", 3)
        if (self.tripped
                and recovery_spaces > 0
                and not game.is_power_suppressed_for(self)):
            self._do_recovery_turn(game, play_by_play_lines, recovery_spaces)
            return
        super().take_turn(game, play_by_play_lines)

    def _do_recovery_turn(self, game, play_by_play_lines, spaces):
        """Hand-rolled phase pipeline for a tripped Penguin turn: same
        non-roll phases as a normal turn, but the main move is a flat
        N-space move (configured by Game.penguin_recovery_move) instead
        of going through the roll pipeline."""
        self.turn_start_position = self.position
        self.last_roll = -1
        self.main_move_multiplier = 1
        self.tripped = False
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) was tripped — Penguin moves {spaces} and recovers."
        )

        # PRE_ROLL still fires (other characters' pre-roll effects, e.g.
        # Cheerleader, Hypnotist, can target Penguin even on a recovery turn).
        game.resolve_phase(PowerPhase.PRE_ROLL, self, play_by_play_lines)

        # Fixed-space move. self.move triggers POST_MOVEMENT board effects
        # (on_enter) and on_being_passed/on_another_player_move reactions
        # internally — same as a normal move would.
        self.move(game, play_by_play_lines, spaces)

        game.resolve_phase(PowerPhase.POST_MOVEMENT, self, play_by_play_lines)

        if not game.is_power_suppressed_for(self):
            self.post_move_ability(game, play_by_play_lines)

        game.resolve_phase(PowerPhase.OTHER_REACTIONS, self, play_by_play_lines)
        game.resolve_phase(PowerPhase.POST_TURN, self, play_by_play_lines)

        game.clear_state_history()
