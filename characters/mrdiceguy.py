# mrdiceguy.py

import random
from collections import Counter
from .base_character import Character

class MrDiceGuy(Character):
    """I roll all six dice for my main move and pick any number that was rolled
    more than once. If no value comes up twice, I don't move.

    Simulator policy: out of all values that appeared 2+ times, the sim picks
    the highest (optimal play for distance — the sim can't model strategic
    positioning like avoiding a portal or trip space)."""

    POWER_PHASES = set()
    EDITION = "v2"

    def main_roll(self, game, play_by_play_lines):
        rolls = [game.roll_die(self, play_by_play_lines) for _ in range(6)]
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
                rolls[idx] = game.roll_die(self, play_by_play_lines)
                play_by_play_lines.append(f"  die rerolled to {rolls[idx]}")

        counts = Counter(rolls)
        doubled = [v for v, c in counts.items() if c >= 2]
        result = max(doubled) if doubled else 0
        note = "highest value rolled 2+ times" if doubled else "no value rolled twice — no move"
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) final dice {sorted(rolls, reverse=True)} -> moves {result} ({note})"
        )
        self.register_ability_use(game, play_by_play_lines, description="MrDiceGuy")
        self.last_roll = result
        return result
