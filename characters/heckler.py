# heckler.py

from .base_character import Character
from power_system import PowerPhase

class Heckler(Character):
    """Moves 2 spaces when another racer ends their turn close to where they started."""

    POWER_PHASES = {PowerPhase.POST_TURN}

    def post_turn_actions(self, game, other_player, play_by_play_lines):
        """Heckler moves 2 if another player ends their turn near their starting space.

        This is called after EVERY player's turn via the POST_TURN phase.
        Checks if the player whose turn just ended is within 1 space of where they started.
        """
        distance = abs(other_player.turn_start_position - other_player.position)
        if distance <= 1:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moves 2 because {other_player.name} ({other_player.piece}) ended their turn close to where they started!"
            )
            self.move(game, play_by_play_lines, 2)
            self.register_ability_use(game, play_by_play_lines, description="Heckler")