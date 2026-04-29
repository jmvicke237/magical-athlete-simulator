# hotel.py

from .base_character import Character

class Hotel(Character):
    """When a racer stops on my space, they pay me 1 bronze chip (1 point).
    If they have no bronze chips, they trip instead.

    Triggers only when another racer's move or jump *ends* at Hotel's space —
    pass-through and Hotel's own movement don't fire it. Strict bronze:
    silver/gold can't be substituted; if no bronze, the racer trips.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        self._maybe_charge(moved_player, game, play_by_play_lines)

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        self._maybe_charge(jumped_player, game, play_by_play_lines)

    def _maybe_charge(self, player, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        if player is self or player.finished or player in game.eliminated_players:
            return
        # No-op moves (clamped, Stickler-blocked) don't count as a "stop"
        if player.position == getattr(player, 'previous_position', player.position):
            return
        # They must end at my space
        if player.position != self.position:
            return

        if player.bronze_chips > 0:
            player.bronze_chips -= 1
            self.bronze_chips += 1
            play_by_play_lines.append(
                f"{player.name} ({player.piece}) stops on {self.name}'s ({self.piece}) "
                f"space and pays 1 bronze chip."
            )
        else:
            player.tripped = True
            play_by_play_lines.append(
                f"{player.name} ({player.piece}) stops on {self.name}'s ({self.piece}) "
                f"space but can't pay — they trip!"
            )
        self.register_ability_use(game, play_by_play_lines, description="Hotel")
