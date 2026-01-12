from .base_character import Character

class ClownCar(Character):  # Renamed class

    POWER_PHASES = set()

    def __init__(self, name, piece):
        super().__init__(name, piece)