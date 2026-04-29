# diceman.py

import random
from collections import Counter
from .base_character import Character

class Diceman(Character):
    """For my main move I roll six dice and move the highest number rolled twice or more.
    If no value comes up twice, I don't move."""

    POWER_PHASES = set()
    EDITION = "v2"

    def main_roll(self, game, play_by_play_lines):
        rolls = [random.randint(1, 6) for _ in range(6)]
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) rolls 6 dice: {sorted(rolls, reverse=True)}"
        )

        # If PartyPooper is in the game, reroll each individual 6 (one PP +1
        # per die rerolled). Loop because rerolled dice might also be 6.
        keep_going = True
        while keep_going:
            sixes_indices = [i for i, v in enumerate(rolls) if v == 6]
            if not sixes_indices:
                break
            for idx in sixes_indices:
                if not self._trigger_party_pooper(game, play_by_play_lines):
                    keep_going = False
                    break
                rolls[idx] = random.randint(1, 6)
                play_by_play_lines.append(f"  die rerolled to {rolls[idx]}")

        counts = Counter(rolls)
        doubled = [v for v, c in counts.items() if c >= 2]
        result = max(doubled) if doubled else 0
        note = "highest value rolled 2+ times" if doubled else "no value rolled twice — no move"
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) final dice {sorted(rolls, reverse=True)} -> moves {result} ({note})"
        )
        self.register_ability_use(game, play_by_play_lines, description="Diceman")
        self.last_roll = result
        return result
