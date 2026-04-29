# stunner.py

from .base_character import Character

class Stunner(Character):
    """Any racer within 1 space of me skips their entire turn — NOT a trip.
    Their take_turn doesn't run at all: no PRE_ROLL, no abilities, no Trip
    recovery. The proximity check lives in Game.run; this class is just a
    marker."""

    POWER_PHASES = set()
    EDITION = "v2"
