# heckler.py

from .base_character import Character

class Heckler(Character):
    def post_turn_actions(self, game, other_player, play_by_play_lines):
        """Heckler moves 2 if another player ends their turn near their starting space."""
        distance = abs(other_player.turn_start_position - other_player.position)
        if distance <= 1:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) moves 2 because {other_player.name} ({other_player.piece}) ended their turn close to where they started!"
            )
            self.move(game, play_by_play_lines, 2)
            self.register_ability_use(game, play_by_play_lines, description="Heckler")