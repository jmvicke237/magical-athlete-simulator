# partypooper.py

from .base_character import Character

class PartyPooper(Character):
    """When another racer rolls a 6 (any d6 roll, not just main move — duels
    too), they must reroll. I move 1 for each forced reroll. Multiple 6s in a
    row loop until a non-6 lands.

    The trigger lives in Character.main_roll so it fires for main rolls,
    Magician/Dicemonger rerolls, and Duelist duel rolls. (Diceman's 6-dice
    mechanic doesn't go through base main_roll, so a Diceman result of 6
    won't trigger PartyPooper.)
    """

    POWER_PHASES = set()
    EDITION = "v2"
