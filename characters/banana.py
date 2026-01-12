# characters/banana.py

from .base_character import Character

class Banana(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        if moved_player != self:
            if self.position > 0 and moved_player.position > self.position and moved_player.previous_position < self.position:
                if not moved_player.tripped:
                    moved_player.trip(game, play_by_play_lines)
                    play_by_play_lines.append(
                        f"{moved_player.name} ({moved_player.piece}) tripped because they passed {self.name} ({self.piece})!"
                    )
                    # self.move(game, play_by_play_lines, -1)
                    self.register_ability_use(game, play_by_play_lines, description="Banana")