# suckerfish.py

from .base_character import Character

class Suckerfish(Character):

    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self._movement_count = 0  # Track movements to prevent loops
        
    def move_with_another(self, moved_player, spaces, game, play_by_play_lines):
        """Move with another racer when they start moving from my space."""
        # Guard against excessive movement
        if game._recursion_depths['movement'] >= game._max_recursion_depth / 2:
            play_by_play_lines.append(f"WARNING: Skipping Suckerfish movement to prevent recursion.")
            return
        
        if self._movement_count >= 3:  # Limit how many times Suckerfish can move in a single turn
            play_by_play_lines.append(f"WARNING: {self.name} (Suckerfish) has moved too many times in this turn. Skipping.")
            return
            
        if moved_player != self and moved_player.previous_position == self.position and not self.finished:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moves with {moved_player.name} ({moved_player.piece}) from Space {self.position} to Space {moved_player.position}."
            )
            self._movement_count += 1
            self.move(game, play_by_play_lines, spaces)
            self.register_ability_use(game, play_by_play_lines, description="Suckerfish")
    
    def take_turn(self, game, play_by_play_lines):
        # Reset movement counter at the start of turn
        self._movement_count = 0
        super().take_turn(game, play_by_play_lines)
