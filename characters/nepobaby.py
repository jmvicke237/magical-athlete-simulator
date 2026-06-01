# nepobaby.py

from .base_character import Character

# Position of the "first corner" on the 30-space board. The board only
# materializes one corner space (config.CORNER_POSITION = 15, the second
# corner); the first corner is a logical landmark used by characters that
# reference it.
FIRST_CORNER_POSITION = 12


class NepoBaby(Character):
    """I start the race on the first corner of the track."""

    POWER_PHASES = set()
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.position = FIRST_CORNER_POSITION
        self.previous_position = self.position
