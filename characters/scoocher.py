#updated
from .base_character import Character
from power_system import PowerPhase

class Scoocher(Character):
    """When another racer's power happens, I move 1."""

    POWER_PHASES = {PowerPhase.OTHER_REACTIONS}

    pass