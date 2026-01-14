# suckerfish.py

from .base_character import Character

class Suckerfish(Character):

    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)
        
    def move_with_another(self, moved_player, spaces, game, play_by_play_lines):
        """Move with another racer when they start moving from my space."""
        # Check for infinite loop using state-based detection
        if game.check_for_state_loop(f"{self.name} ({self.piece}) - Suckerfish", play_by_play_lines):
            return

        if moved_player != self and moved_player.previous_position == self.position and not self.finished:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moves with {moved_player.name} ({moved_player.piece}) from Space {self.position} to Space {moved_player.position}."
            )
            self.move(game, play_by_play_lines, spaces)
            self.register_ability_use(game, play_by_play_lines, description="Suckerfish")
