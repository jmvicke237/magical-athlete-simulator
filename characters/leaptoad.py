# leaptoad.py

from .base_character import Character

class Leaptoad(Character):
    """I skip Spaces with other racers on them when Moving."""
    def move(self, game, play_by_play_lines, spaces):
        original_position = self.position
        new_position = original_position
        skipped_spaces = False

        # Get the direction of movement (1 for forward, -1 for backward)
        direction = 1 if spaces > 0 else -1 if spaces < 0 else 0
        
        # Calculate movement, skipping occupied spaces
        for _ in range(abs(spaces)):
            new_position += direction
            if new_position >= game.board.length:
                new_position = game.board.length
                break
            # Check if the next space is occupied (excluding Leaptoad itself)
            occupied = False
            for other_player in game.players:
                if other_player != self and other_player.position == new_position:
                    occupied = True
                    break
            if occupied:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) skipped a space at {new_position}."
                )
                new_position += direction
                skipped_spaces = True
                continue  # Skip this space
        #Leap to 
        self.position = new_position

        if self.position >= game.board.length:
            game.finish_player(self, play_by_play_lines)
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moved from {original_position} to {self.position} and finished!"
            )
        else:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moved from {original_position} to {self.position}"
            )
            current_space = game.board.spaces[self.position]
            current_space.on_enter(self, game, play_by_play_lines)
          
        # Move Suckerfish before checking for another_player_move to avoid conflicts with Romantic etc
        for p in game.players:
            if p.piece == "Suckerfish":
                p.move_with_another(self, spaces, game, play_by_play_lines)
        
        for other_player in game.players:
            if other_player != self:
                other_player.on_another_player_move(self, game, play_by_play_lines)
        
        if skipped_spaces:
            self.register_ability_use(game, play_by_play_lines, description="Leaptoad")