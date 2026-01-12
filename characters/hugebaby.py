# hugebaby.py

from .base_character import Character

class HugeBaby(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        # Dictionary to track player interactions with HugeBaby to prevent infinite loops
        self.player_interaction_count = {}

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        self._check_shared_space(game, play_by_play_lines)

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        self._check_shared_space(game, play_by_play_lines)

    def move(self, game, play_by_play_lines, spaces):
        super().move(game, play_by_play_lines, spaces)
        self._check_shared_space(game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        super().jump(game, position, play_by_play_lines)
        self._check_shared_space(game, play_by_play_lines)
    
    def _check_shared_space(self, game, play_by_play_lines):
        """If any player (including Huge Baby) is on another player's space (other than the start), the other player gets pushed back."""
        from debug_utils import logger
        
        if self.position <= 0:
            return
            
        # Check if there's a move forward space that could cause an infinite loop
        # Wild board has move space at position 11 that moves forward 1 and creates loop with HugeBaby at position 12
        is_potential_loop_space = False
        if self.position > 0 and self.position < game.board.length:
            if self.position == 12 and game.board.board_type == "Wild":
                # Position 11 has a move forward 1 effect
                is_potential_loop_space = True
                
        # Check for players on same space
        for other_player in game.players:
            if other_player != self and other_player.position == self.position:
                # Create a unique key for this player in this position
                player_key = f"{other_player.piece}_{self.position}"
                
                # Check if we're in an infinite loop situation
                self.player_interaction_count[player_key] = self.player_interaction_count.get(player_key, 0) + 1
                interaction_count = self.player_interaction_count[player_key]
                
                # Use a more aggressive threshold for known problematic spaces
                max_interactions = 2 if is_potential_loop_space else 3
                
                # If we've pushed the same player from the same space too many times, break the loop
                if interaction_count > max_interactions:
                    # Only log warnings when we're breaking a loop
                    logger.warning(f"Breaking potential infinite loop: {other_player.name} ({other_player.piece}) with HugeBaby at position {self.position}")
                    play_by_play_lines.append(f"{other_player.name} ({other_player.piece}) broke free from the loop with {self.name} ({self.piece})!")
                    
                    # Reset the counter for future encounters
                    self.player_interaction_count[player_key] = 0
                    
                    # Register ability use still to track that the ability triggered
                    if other_player.piece != "Scoocher":
                        self.register_ability_use(game, play_by_play_lines, description="Hugebaby")
                    return

                # Normal push back behavior
                other_player.move(game, play_by_play_lines, -1)
                play_by_play_lines.append(f"{other_player.name} ({other_player.piece}) was pushed back by {self.name} ({self.piece})!")
                
                if other_player.piece != "Scoocher":
                    self.register_ability_use(game, play_by_play_lines, description="Hugebaby")
