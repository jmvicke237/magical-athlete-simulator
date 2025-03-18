# characters/romantic.py

from .base_character import Character

"""Moves 3 spaces when any player Stops on a Space with exactly one other racer."""

class Romantic(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self._trigger_depth = 0  # Track recursion depth
    
    def move(self, game, play_by_play_lines, spaces):
        # Increment trigger depth before move
        self._trigger_depth += 1
        
        # Call the parent's move method
        super().move(game, play_by_play_lines, spaces)
        
        # Only trigger ability if we're not too deep in recursion (limit to one level)
        if self._trigger_depth == 1:
            self.check_for_romantic(self, game, play_by_play_lines)
        
        # Decrement trigger depth after move
        self._trigger_depth -= 1
    
    def jump(self, game, position, play_by_play_lines):
        # Increment trigger depth before jump
        self._trigger_depth += 1
        
        # Call the parent's jump method
        super().jump(game, position, play_by_play_lines)
        
        # Only trigger ability if we're not too deep in recursion (limit to one level)
        if self._trigger_depth == 1:
            self.check_for_romantic(self, game, play_by_play_lines)
        
        # Decrement trigger depth after jump
        self._trigger_depth -= 1
    
    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        self.check_for_romantic(moved_player, game, play_by_play_lines)
            
    def on_another_player_jump(self, moved_player, game, play_by_play_lines):
        self.check_for_romantic(moved_player, game, play_by_play_lines)
    
    def check_for_romantic(self, moved_player, game, play_by_play_lines):
        space_mates = moved_player.check_for_share_space(game)
        if len(space_mates) == 1:
            if moved_player.piece != "HugeBaby" and space_mates[0].piece != "HugeBaby":
                play_by_play_lines.append(f"{self.name} ({self.piece}) moved 3 because {moved_player.name} ({moved_player.piece}) shared a space with exactly one player.")
                self.move(game, play_by_play_lines, 3)
                game.trigger_scoocher(play_by_play_lines) #Scoocher 