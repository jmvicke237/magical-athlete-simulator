from characters.base_character import Character

class Sisyphis(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        # Start with 4 bronze point chips
        self.bronze_chips = 4

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        # Only trigger when this character rolls
        if roller == self and roll == 1:
            self.register_ability_use(game, play_by_play_lines, "Rolled a 1, going back to start")
            
            # Lose a bronze chip if available
            if self.bronze_chips > 0:
                self.bronze_chips -= 1
                play_by_play_lines.append(f"{self.name} ({self.piece}) lost a bronze chip. Remaining: {self.bronze_chips}")
            else:
                play_by_play_lines.append(f"{self.name} ({self.piece}) has no bronze chips left.")
            
            # Jump back to start space
            self.jump(game, 0, play_by_play_lines)