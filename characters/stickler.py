# characters/stickler.py

from .base_character import Character

class Stickler(Character):
    """Other racers can only cross the finish line by moving the exact amount they need. If they overshoot, they don't move."""

    POWER_PHASES = set()

    def __init__(self, name, piece):
        super().__init__(name, piece)

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        """Check if another player is about to overshoot the finish line."""
        # This character's power is passive and affects the game mechanics
        # The actual implementation would need to be in the base Character.move() method
        # to check if Stickler is in the game before allowing a player to finish
        # For now, this is a placeholder as the logic needs to be integrated into
        # the core movement system
        pass

    @staticmethod
    def is_in_game(game):
        """Check if Stickler is in this game."""
        for player in game.players:
            if player.piece == "Stickler" and not player.finished:
                return True
        return False

    @staticmethod
    def would_overshoot(current_position, spaces, finish_line):
        """Check if a move would overshoot the finish line."""
        return current_position + spaces > finish_line
