from .base_character import Character

class Egg(Character):  # Renamed class
    def __init__(self, name, piece):
        super().__init__(name, piece)