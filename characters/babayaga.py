# characters/babayaga.py
from .base_character import Character

class BabaYaga(Character):

    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def move(self, game, play_by_play_lines, spaces):
        # Capture position first. "Move 0 isn't a Move" (and a Stickler-blocked
        # move leaves the position unchanged too) — in either case BabaYaga
        # never actually stopped on a new space, so it must NOT trip whoever
        # is sharing its space. Only trip when the move really happened, i.e.
        # the position changed.
        pre = self.position
        super().move(game, play_by_play_lines, spaces)
        if self.position != pre:
            self._check_trip(game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        # Same rule for warps: a no-op jump (to the space we're already on)
        # isn't a stop, so it doesn't trip. A real warp does count as stopping.
        pre = self.position
        super().jump(game, position, play_by_play_lines)
        if self.position != pre:
            self._check_trip(game, play_by_play_lines)
        
    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        if moved_player != self:
            self._check_trip(game, play_by_play_lines)

    def _check_trip(self, game, play_by_play_lines):
        """Checks for and applies Baba Yaga's tripping ability."""
        if self.position > 0:  # Not on the starting space
            for other_player in game.players:
                if other_player != self and other_player.position == self.position:
                    if not other_player.tripped:
                        other_player.trip(game, play_by_play_lines)
                        play_by_play_lines.append(
                            f"{self.name} ({self.piece}) tripped {other_player.name} ({other_player.piece})!"
                        )
                        self.register_ability_use(game, play_by_play_lines, description="BabaYaga")