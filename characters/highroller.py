# highroller.py

import random
from .base_character import Character

class HighRoller(Character):
    """After I roll for my main move, I keep rolling and adding each amount.
    If I ever roll lower than my last successful roll, I trip (skip my next
    main move) and don't move this turn. I always keep rolling until I have
    at least `game.highroller_threshold` (default 8) movement."""

    POWER_PHASES = set()
    EDITION = "v2"

    def main_roll(self, game, play_by_play_lines):
        # Antimag: HighRoller's override is a power. Fall back to base d6 if suppressed.
        if game.is_power_suppressed_for(self):
            return Character.main_roll(self, game, play_by_play_lines)

        threshold = getattr(game, 'highroller_threshold', 8)
        last_roll = None
        total = 0
        first_log = True

        while True:
            new_roll = random.randint(1, 6)
            # PartyPooper hook on this individual die
            while new_roll == 6 and self._trigger_party_pooper(game, play_by_play_lines):
                new_roll = random.randint(1, 6)

            if first_log:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) rolls {new_roll} (target ≥{threshold})"
                )
                first_log = False
            else:
                play_by_play_lines.append(
                    f"  {self.name} rolls again: {new_roll} (running total: {total + new_roll if (last_roll is None or new_roll >= last_roll) else 'tripped'})"
                )

            if last_roll is not None and new_roll < last_roll:
                play_by_play_lines.append(
                    f"  {new_roll} < {last_roll} — HighRoller trips and doesn't move this turn!"
                )
                self.tripped = True
                self.skip_main_move = True
                self.last_roll = 0
                self.register_ability_use(game, play_by_play_lines, description="HighRoller tripped")
                return 0

            total += new_roll
            last_roll = new_roll

            if total >= threshold:
                break

        play_by_play_lines.append(
            f"  HighRoller hit target — moves {total}"
        )
        self.last_roll = total
        self.register_ability_use(game, play_by_play_lines, description="HighRoller")
        return total
