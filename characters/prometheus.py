# prometheus.py

from .base_character import Character
from power_system import PowerPhase

class Prometheus(Character):
    """+1 to my main move for each point I (the racer) currently have. I'm
    eliminated if I'm more than `prometheus_threshold` spaces ahead. Whether
    the check fires at the start ("start") or end ("end") of my turn is
    controlled by `game.prometheus_check_timing`. Points only count if I
    earned them this race."""

    POWER_PHASES = {PowerPhase.PRE_ROLL, PowerPhase.POST_TURN, PowerPhase.ROLL_MODIFICATION}
    EDITION = "v2"

    def pre_move_action(self, game, play_by_play_lines):
        if getattr(game, 'prometheus_check_timing', 'end') != 'start':
            return
        # Fires even when tripped — Prometheus can be struck down regardless
        # of whether they would otherwise move this turn.
        self._maybe_self_eliminate(game, play_by_play_lines)

    def post_turn_actions(self, game, current_player, play_by_play_lines):
        if current_player is not self:
            return
        if getattr(game, 'prometheus_check_timing', 'end') != 'end':
            return
        self._maybe_self_eliminate(game, play_by_play_lines)

    def _maybe_self_eliminate(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return

        others = [
            p for p in game.players
            if p is not self and p not in game.eliminated_players
        ]
        if not others:
            return  # alone — nothing to be ahead of

        # Compare against all other non-eliminated racers (finished count —
        # they're at the finish line and definitely "ahead").
        max_other = max(p.position for p in others)
        lead = self.position - max_other
        threshold = getattr(game, 'prometheus_threshold', 3)
        if lead > threshold:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) flew too high — {lead} spaces ahead "
                f"(threshold {threshold}). Prometheus is struck down!"
            )
            game.eliminate_player(self, play_by_play_lines)
            self.skip_main_move = True  # safe even if check is at end of turn
            self.register_ability_use(game, play_by_play_lines, description="Prometheus eliminated")

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        if (other_player is not self
                or self.finished
                or self in game.eliminated_players):
            return roll
        points = self.gold_chips * 5 + self.silver_chips * 3 + self.bronze_chips
        if points == 0:
            return roll
        new_roll = roll + points
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) gets +{points} (one per point earned). "
            f"Roll: {roll} -> {new_roll}"
        )
        self.register_ability_use(game, play_by_play_lines, description="Prometheus")
        return new_roll
