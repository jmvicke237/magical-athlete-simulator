# suckerfish.py

from .base_character import Character

class Suckerfish(Character):

    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def move_with_another(self, moved_player, spaces, game, play_by_play_lines):
        """Move with another racer when they start moving from my space.

        Note: This updates position directly without calling move() to avoid
        triggering cascading Suckerfish checks (which would cause infinite recursion).
        However, it still triggers space effects and other follow-up actions.
        """
        if moved_player != self and moved_player.previous_position == self.position and not self.finished:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moves with {moved_player.name} ({moved_player.piece}) from Space {self.position} to Space {moved_player.position}."
            )
            # Update position directly without triggering move() logic
            self.previous_position = self.position
            self.position = moved_player.position

            # Check if finished
            if self.position >= game.board.length:
                self.position = game.board.length
                game.finish_player(self, play_by_play_lines)
            else:
                # Trigger board space effects (arrows, trips, stars, etc.)
                current_space = game.board.spaces[self.position]
                current_space.on_enter(self, game, play_by_play_lines)

            self.register_ability_use(game, play_by_play_lines, description="Suckerfish")
