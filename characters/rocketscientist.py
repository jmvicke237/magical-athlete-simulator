# rocketscientist.py

from .base_character import Character

class RocketScientist(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.has_doubled = False
    
    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Rocket Scientist doubles the roll, but trips if they do."""
        if other_player == self and roll >= 4:
            doubled_roll = roll * 2
            self.trip(game, play_by_play_lines) #Force that ability
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) doubles their roll to {doubled_roll}, but is now tripped!"
            )
            self.register_ability_use(game, play_by_play_lines, description="RocketScientist")
            return doubled_roll
        return roll