# streaker.py

from .base_character import Character


class Streaker(Character):
    """When I pass any racers during my main move, I get 1 bronze chip. Just 1
    chip per main move regardless of how many racers I pass.

    Implementation: track a "main move window" via two flags.

      - main_roll() sets _movement_pending = True (the dice roll just landed;
        the MOVEMENT phase will dispatch self.move() next).
      - The outer self.move() call clears _movement_pending and sets
        _in_main_move = True for its duration; cascaded moves inside the same
        move() call (Wild +/-N spaces, Sportals portal jumps) stay inside the
        window and still count.
      - detect_passes only flags a pass when _in_main_move is True, so pulls
        from PartyAnimal-style pre-move actions or pushes from other racers'
        turns don't qualify.

    Cleanup: take_turn resets all flags at the start and clears
    _movement_pending at the end too, so a skipped main move (Inchworm,
    trip carry-over) doesn't leak the flag into a non-main move() call.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self._passed_this_turn = False
        self._movement_pending = False
        self._in_main_move = False

    def take_turn(self, game, play_by_play_lines):
        self._passed_this_turn = False
        self._movement_pending = False
        self._in_main_move = False
        super().take_turn(game, play_by_play_lines)
        # Safety: if the main move was skipped after main_roll set the flag,
        # don't let it leak into a subsequent non-main move() call.
        self._movement_pending = False

    def main_roll(self, game, play_by_play_lines):
        self._movement_pending = True
        return super().main_roll(game, play_by_play_lines)

    def move(self, game, play_by_play_lines, spaces):
        is_main_move_outer = self._movement_pending and not self._in_main_move
        if is_main_move_outer:
            self._movement_pending = False
            self._in_main_move = True
        try:
            super().move(game, play_by_play_lines, spaces)
        finally:
            if is_main_move_outer:
                self._in_main_move = False

    def detect_passes(self, game, start_position, end_position):
        passed = super().detect_passes(game, start_position, end_position)
        if passed and self._in_main_move:
            self._passed_this_turn = True
        return passed

    def post_move_ability(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        if self._passed_this_turn:
            self.bronze_chips += 1
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) streaks past someone — +1 bronze chip!"
            )
            self.register_ability_use(game, play_by_play_lines, description="Streaker")
            self._passed_this_turn = False
