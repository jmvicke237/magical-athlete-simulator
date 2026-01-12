# characters/boogeyman.py

from .base_character import Character

class Boogeyman(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.has_used_ability = False

    def pre_move_action(self, game, play_by_play_lines):
        if not self.has_used_ability:
            leader = None
            max_position = -1
            for player in game.players:
                if not player.finished and player.position > max_position:
                    max_position = player.position
                    leader = player

            if leader:
                target_position = max(0, leader.position - 1) # Simplified
                if self.position != target_position: # Don't jump if already there
                    if target_position >= game.board.length - 6:
                        play_by_play_lines.append(f"{self.name} ({self.piece}) uses their ability to jump behind the leader!")
                        self.jump(game, target_position, play_by_play_lines)
                        self.has_used_ability = True
                        self.register_ability_use(game, play_by_play_lines, description="Boogeyman")