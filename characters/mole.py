# mole.py

import random
from .base_character import Character

class Mole(Character):
    """When a racer stops on my space, or I stop on theirs, I warp to the
    space in front of the lead racer. Tied leaders → random pick."""

    POWER_PHASES = set()
    EDITION = "v2"

    def move(self, game, play_by_play_lines, spaces):
        pre = self.position
        super().move(game, play_by_play_lines, spaces)
        # Only fire if a new stop event happened (position actually changed).
        # A clamped-to-zero move or a state-loop-blocked super call leaves
        # position unchanged — no new "stop on theirs" event per spec.
        if self.position != pre:
            self._maybe_warp(game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        pre = self.position
        super().jump(game, position, play_by_play_lines)
        if self.position != pre:
            self._maybe_warp(game, play_by_play_lines)

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        # Only fire if the other player actually moved onto my space (not if
        # they were already here and their move was a no-op).
        if (moved_player.position != getattr(moved_player, 'previous_position', moved_player.position)
                and moved_player.position == self.position):
            self._maybe_warp(game, play_by_play_lines)

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        if (jumped_player.position != getattr(jumped_player, 'previous_position', jumped_player.position)
                and jumped_player.position == self.position):
            self._maybe_warp(game, play_by_play_lines)

    # Max chained warps from a single outer trigger. Each cascade level adds
    # ~5–7 stack frames (Mole.jump → super.jump → on_enter → Mole.move →
    # super.move → _maybe_warp → next), so 150 stays well under Python's
    # default 1000-frame recursion limit. In practice, any cascade that
    # reaches this depth is almost certainly a non-terminating oscillation —
    # legitimate cascades resolve in single-digit depths.
    _MAX_CASCADE_DEPTH = 150

    def _maybe_warp(self, game, play_by_play_lines):
        depth = getattr(self, '_warp_cascade_depth', 0)
        if depth >= self._MAX_CASCADE_DEPTH:
            return  # Backstop against runaway cascades (state-loop may miss subtle cycles)
        if self.finished or self in game.eliminated_players:
            return
        # AntimagicalAthlete: Mole's warp is a power; suppressed when ahead.
        if game.is_power_suppressed_for(self):
            return

        # Need at least one active racer sharing my space to fire.
        space_mates = [
            p for p in game.players
            if p is not self
            and p.position == self.position
            and not p.finished
            and p not in game.eliminated_players
        ]
        if not space_mates:
            return

        # Lead racer is the highest-positioned active racer (Mole included).
        active = [
            p for p in game.players
            if not p.finished and p not in game.eliminated_players
        ]
        if not active:
            return

        max_pos = max(p.position for p in active)
        target = max_pos + 1
        if target > game.board.length:
            return  # No space in front of the finish line
        if target == self.position:
            return  # Already there — avoid spinning in place

        leaders = [p for p in active if p.position == max_pos]
        leader = random.choice(leaders)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) warps to space {target} "
            f"(in front of lead racer {leader.name} ({leader.piece}))."
        )
        self._warp_cascade_depth = depth + 1
        try:
            self.jump(game, target, play_by_play_lines)
            self.register_ability_use(game, play_by_play_lines, description="Mole")
        finally:
            self._warp_cascade_depth = depth
