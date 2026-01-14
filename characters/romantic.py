from .base_character import Character
from power_system import PowerPhase

"""Moves 3 spaces when any player Stops on a Space with exactly one other ra
    POWER_PHASES = {PowerPhase.OTHER_REACTIONS}
cer."""

class Romantic(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def move(self, game, play_by_play_lines, spaces):
        # Record position before move
        position_before = self.position

        # Call the parent's move method (handles state-based loop detection)
        super().move(game, play_by_play_lines, spaces)

        # Only check for romantic ability if we actually moved
        # (i.e., not stopped by loop detection or other early returns)
        if self.position != position_before:
            self.check_for_romantic(self, game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        # Record position before jump
        position_before = self.position

        # Call the parent's jump method (handles state-based loop detection)
        super().jump(game, position, play_by_play_lines)

        # Only check for romantic ability if we actually jumped
        # (i.e., not stopped by loop detection or other early returns)
        if self.position != position_before:
            self.check_for_romantic(self, game, play_by_play_lines)

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        self.check_for_romantic(moved_player, game, play_by_play_lines)

    def on_another_player_jump(self, moved_player, game, play_by_play_lines):
        self.check_for_romantic(moved_player, game, play_by_play_lines)

    def check_for_romantic(self, moved_player, game, play_by_play_lines):
        # State-based loop detection in move() will catch infinite loops
            
        space_mates = moved_player.check_for_share_space(game)
        if len(space_mates) == 1:
            if moved_player.piece != "HugeBaby" and space_mates[0].piece != "HugeBaby":
                play_by_play_lines.append(f"{self.name} ({self.piece}) moved 2 because {moved_player.name} ({moved_player.piece}) shared a space with exactly one player.")
                self.move(game, play_by_play_lines, 2)
                self.register_ability_use(game, play_by_play_lines, description="Romantic")