# thirdwheel.py

from .base_character import Character

class ThirdWheel(Character):
    def pre_move_action(self, game, play_by_play_lines):
        """Warps to any Space with exactly 2 racers on it."""

        target_space = None
        max_space = -1
        # Iterate through the board backwards to find the *furthest* target space
        for i in range(game.board.length -1, -1, -1):
            # Check each space on the board.
            players_on_space = 0
            for player in game.players:
                if player != self and player.position == i:
                    players_on_space += 1
            if players_on_space == 2:  # The code finds one that is happening
                target_space = i
                break  # If there, there is only one.

        # If a target space is found, Warp to it.
        if target_space is not None and target_space > self.position:
            old_space = self.position
            play_by_play_lines.append(f"{self.name} ({self.piece}) Warps to space {target_space} with exactly 2 racers on it from {old_space}")
            self.jump(game, target_space, play_by_play_lines)
            self.register_ability_use(game, play_by_play_lines, description="ThirdWheel")