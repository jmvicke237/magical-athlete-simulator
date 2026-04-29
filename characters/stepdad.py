# stepdad.py

from .base_character import Character
from power_system import PowerPhase

class Stepdad(Character):
    """The racer to my left gets +2 to their main move. If they win the race,
    I get 3 points (3 bronze chips).

    "Left" = immediate previous in turn_order (the engine has no fixed seating
    model). The win bonus fires once per race regardless of Stepdad's own
    finished/eliminated state.
    """

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self._stepchild_win_awarded = False

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        if self.finished or self in game.eliminated_players:
            return roll
        if not self._is_racer_to_my_left(game, other_player):
            return roll
        new_roll = roll + 2
        play_by_play_lines.append(
            f"{other_player.name} ({other_player.piece}) gets +2 from {self.name}'s "
            f"stepdad bonus. Roll: {roll} -> {new_roll}"
        )
        self.register_ability_use(game, play_by_play_lines, description="Stepdad bonus")
        return new_roll

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        self._maybe_award_stepchild_win(game, play_by_play_lines)

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        self._maybe_award_stepchild_win(game, play_by_play_lines)

    def _maybe_award_stepchild_win(self, game, play_by_play_lines):
        if self._stepchild_win_awarded:
            return
        # Eliminated Stepdad's power is fully off — no win bonus either.
        if self in game.eliminated_players:
            return
        left = self._racer_to_my_left(game)
        if left is None:
            return
        # Win = finished 1st = has the gold chip awarded by finish_player.
        if not left.finished or left.gold_chips != 1:
            return
        self.bronze_chips += 3
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) gets 3 bronze chips because their stepchild "
            f"{left.name} ({left.piece}) won the race!"
        )
        self._stepchild_win_awarded = True
        self.register_ability_use(game, play_by_play_lines, description="Stepdad win bonus")

    def _racer_to_my_left(self, game):
        """Walk backwards in turn_order, wrapping, until we find a non-eliminated
        racer. Eliminated racers are skipped so the +2 (and the win bonus)
        cascade past them to the next previous player. Returns None if no
        eligible left racer exists."""
        n = len(game.turn_order)
        if n <= 1:
            return None
        try:
            my_player_idx = game.players.index(self)
            my_order_idx = game.turn_order.index(my_player_idx)
        except ValueError:
            return None
        for offset in range(1, n + 1):
            prev_idx = (my_order_idx - offset) % n
            candidate = game.players[game.turn_order[prev_idx]]
            if candidate is self:
                continue
            if candidate in game.eliminated_players:
                continue
            return candidate
        return None

    def _is_racer_to_my_left(self, game, candidate):
        return self._racer_to_my_left(game) is candidate
