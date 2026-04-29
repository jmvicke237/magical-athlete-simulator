# showboat.py

from .base_character import Character

class ShowBoat(Character):
    """When I pass any racers during my turn, I get 1 bronze chip. Just 1
    chip per turn regardless of how many racers I pass.

    Implementation: detect_passes flips a flag whenever any forward pass
    is registered during my movement (main move and any cascaded on_enter
    move effects). post_move_ability awards the chip and resets the flag.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self._passed_this_turn = False

    def take_turn(self, game, play_by_play_lines):
        # Reset at start of every turn so stale flags don't carry over
        # (e.g., if Antimag suppression skipped post_move_ability previously).
        self._passed_this_turn = False
        super().take_turn(game, play_by_play_lines)

    def detect_passes(self, game, start_position, end_position):
        passed = super().detect_passes(game, start_position, end_position)
        if passed:
            self._passed_this_turn = True
        return passed

    def post_move_ability(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        if self._passed_this_turn:
            self.bronze_chips += 1
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) showboats — passed at least one racer, +1 bronze chip!"
            )
            self.register_ability_use(game, play_by_play_lines, description="ShowBoat")
            self._passed_this_turn = False
