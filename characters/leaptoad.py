# leaptoad.py

from .base_character import Character

class Leaptoad(Character):
    """I skip Spaces with other racers on them when Moving."""

    POWER_PHASES = set()
    def move(self, game, play_by_play_lines, spaces):
        """Move LeapToad, skipping occupied spaces, with recursion depth tracking."""
        # Rule: "Move 0" does not count as moving and should not trigger abilities
        if spaces == 0:
            return

        # Import the logger for recursion tracking
        from debug_utils import log_recursion_state, logger

        # Log state only when approaching recursion limits
        log_recursion_state(game, "leap move", self)
        
        # Guard against excessive recursion
        if game._recursion_depths['movement'] >= game._max_recursion_depth:
            play_by_play_lines.append(f"WARNING: Maximum movement recursion depth ({game._max_recursion_depth}) reached for {self.name} ({self.piece})! Stopping recursion.")
            
            # Log critical info about the recursion
            position_info = f"position={self.position}, spaces={spaces}"
            logger.error(f"Movement recursion limit reached for {self.name} ({self.piece}) at {position_info}")
            return
        
        # Increment recursion counter
        game._recursion_depths['movement'] += 1
        
        try:
            if self.finished:
                return
                
            original_position = self.position
            new_position = original_position
            skipped_spaces = False
            
            # Record previous position for tracking
            self.previous_position = original_position

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
            
            # Set the new position
            self.position = new_position

            if self.position >= game.board.length:
                self.position = game.board.length
                game.finish_player(self, play_by_play_lines)
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) moved from {original_position} to {self.position} and finished!"
                )
            else:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) moved from {original_position} to {self.position}"
                )

                # Trigger board space effects
                current_space = game.board.spaces[self.position]
                current_space.on_enter(self, game, play_by_play_lines)

            # Detect and notify passed racers
            passed_racers = self.detect_passes(game, original_position, self.position)
            for passed_racer in passed_racers:
                passed_racer.on_being_passed(self, game, play_by_play_lines)

            # Move Suckerfish before checking for another_player_move to avoid conflicts with Romantic etc
            for p in game.players:
                if p.piece == "Suckerfish" and p != self:
                    p.move_with_another(self, spaces, game, play_by_play_lines)

            # Notify other players about the movement
            for other_player in game.players:
                if other_player != self:
                    other_player.on_another_player_move(self, game, play_by_play_lines)
            
            # Register ability use if spaces were skipped
            if skipped_spaces:
                self.register_ability_use(game, play_by_play_lines, description="Leaptoad")
        finally:
            # Decrement recursion counter
            game._recursion_depths['movement'] -= 1