# hogknight.py

from .base_character import Character
from power_system import PowerPhase


class HogKnight(Character):
    """I start the race on a hog. The hog gives its rider +2 to their main move.
    When a racer stops on the hog's space (or the hog stops on theirs), they
    take the hog. If the hog stops on multiple racers, the next in turn order
    after the previous rider steals it."""

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}
    EDITION = "v2"

    # ----- Hog state lives on the game so it survives transfers -----

    def _get_hog_state(self, game):
        """Lazy-init: HogKnight starts as the rider at HogKnight's position."""
        if not hasattr(game, '_hog_state'):
            game._hog_state = {
                'rider': self,
                'position': self.position,
                'active': True,
            }
        return game._hog_state

    def _deactivate_if_rider_out(self, game, state, play_by_play_lines):
        rider = state['rider']
        if rider.finished or rider in game.eliminated_players:
            state['active'] = False
            play_by_play_lines.append(
                f"  The hog is left behind (rider {rider.name} ({rider.piece}) is out)."
            )
            return True
        return False

    # ----- ROLL_MODIFICATION: +2 to whoever currently holds the hog -----

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        state = self._get_hog_state(game)
        if not state['active']:
            return roll
        if self._deactivate_if_rider_out(game, state, play_by_play_lines):
            return roll
        if state['rider'] is not other_player:
            return roll
        new_roll = roll + 2
        play_by_play_lines.append(
            f"{other_player.name} ({other_player.piece}) gets +2 from the hog. "
            f"Roll: {roll} -> {new_roll}"
        )
        self.register_ability_use(game, play_by_play_lines, description="HogKnight (hog bonus)")
        return new_roll

    # ----- Movement hooks: handle transfers -----

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        # Other players' moves can trigger a transfer (they land on the hog,
        # or — if they're the current rider — the hog moves with them).
        self._handle_hog_transfer(game, moved_player, play_by_play_lines)

    def move(self, game, play_by_play_lines, spaces):
        # HogKnight's own move doesn't fire on_another_player_move on self,
        # so we explicitly handle it here.
        super().move(game, play_by_play_lines, spaces)
        self._handle_hog_transfer(game, self, play_by_play_lines)

    # ----- Transfer logic -----

    def _handle_hog_transfer(self, game, moved_player, play_by_play_lines):
        state = self._get_hog_state(game)
        if not state['active']:
            return
        if self._deactivate_if_rider_out(game, state, play_by_play_lines):
            return

        rider = state['rider']

        if moved_player is rider:
            # Rider moved → hog moves with them. Check if any other racers are
            # at the new space.
            state['position'] = rider.position
            candidates = [
                p for p in game.players
                if p is not rider
                and not p.finished
                and p not in game.eliminated_players
                and p.position == rider.position
            ]
            if candidates:
                new_rider = self._pick_next_in_turn_order(game, rider, candidates)
                if new_rider is not None:
                    self._transfer_hog(state, new_rider, play_by_play_lines, game)
        else:
            # Non-rider moved. Did they land on the hog's space?
            if moved_player.position == state['position']:
                self._transfer_hog(state, moved_player, play_by_play_lines, game)

    def _transfer_hog(self, state, new_rider, play_by_play_lines, game):
        old_rider = state['rider']
        if new_rider is old_rider:
            return
        play_by_play_lines.append(
            f"  {new_rider.name} ({new_rider.piece}) takes the hog from "
            f"{old_rider.name} ({old_rider.piece})!"
        )
        state['rider'] = new_rider
        state['position'] = new_rider.position
        self.register_ability_use(game, play_by_play_lines, description="HogKnight (hog transferred)")

    def _pick_next_in_turn_order(self, game, current_rider, candidates):
        """Return the candidate that comes first in turn order starting from
        the position after the current rider."""
        try:
            rider_player_idx = game.players.index(current_rider)
            rider_order_pos = game.turn_order.index(rider_player_idx)
        except ValueError:
            return candidates[0] if candidates else None
        n = len(game.turn_order)
        for offset in range(1, n + 1):
            check_idx = (rider_order_pos + offset) % n
            candidate = game.players[game.turn_order[check_idx]]
            if candidate in candidates:
                return candidate
        return None
