# mole.py

from .base_character import Character


class Mole(Character):
    """If there are no racers within 1 space of me, I move 6 for my main move.

    Sharing my space (distance 0) and immediately adjacent (distance 1)
    both count as "within 1" — so Mole only gets the bonus when alone in
    a 3-space window. Otherwise Mole rolls a normal d6 like everyone else.

    Implementation: main_roll override. Returns 6 directly (no die roll)
    when the proximity check finds zero other active racers in the
    [position-1, position+1] window. Doesn't go through game.roll_die
    because the 6 isn't actually a die — same pattern as Legs's
    always-5. Other phases (DIE_ROLL_TRIGGER, ROLL_MODIFICATION) still
    operate on the returned 6 the same way they would on a normal roll.

    Antimag interaction: Mole's "move 6" is a power, so a Mole strictly
    ahead of an active AntimagicalAthlete loses it and falls back to
    base.main_roll (vanilla d6). The Antimag main-move penalty then
    applies on top in base.take_turn as usual.

    Stunner interaction: Stunner-within-1 means there IS a racer within
    1 of Mole, so Mole's power doesn't trigger — Mole rolls normally
    via base.main_roll, which funnels through game.roll_die, which
    forces a 1. Mole-isolated-from-Stunner means no one is within 1 of
    Mole (including Stunner), so the move-6 bonus fires unblocked.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def main_roll(self, game, play_by_play_lines):
        # Antimag: Mole's override is a power. Fall back to base d6 if suppressed.
        if game.is_power_suppressed_for(self):
            return Character.main_roll(self, game, play_by_play_lines)

        if self._has_neighbor_within_one(game):
            # Someone's near me — no isolation bonus, roll normally.
            return Character.main_roll(self, game, play_by_play_lines)

        play_by_play_lines.append(
            f"{self.name} ({self.piece}) is isolated (no racers within 1) — moves 6."
        )
        self.last_roll = 6
        self.register_ability_use(game, play_by_play_lines, description="Mole isolated")
        return 6

    def _has_neighbor_within_one(self, game):
        for p in game.players:
            if p is self:
                continue
            if p.finished or p in game.eliminated_players:
                continue
            if abs(p.position - self.position) <= 1:
                return True
        return False
