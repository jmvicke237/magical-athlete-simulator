# flipflop.py

from .base_character import Character

class FlipFlop(Character):
    def pre_move_action(self, game, play_by_play_lines):
        """
        FlipFlop swaps places with the furthest player who is at least 4 spaces ahead.
        If no such player exists, the FlipFlop will roll as usual.
        """
        # Find all players at least 4 spaces ahead
        candidates = [
            player
            for player in game.players
            if player != self
            and player.position - self.position >= 4
            and not player.finished
        ]

        # If there are valid candidates, swap with the furthest one
        if candidates:
            # Find the furthest player ahead
            target = max(candidates, key=lambda player: player.position)

            # Store positions *before* the swap
            original_flipflop_position = self.position
            original_target_position = target.position

            # Perform the swap using the jump function
            self.jump(game, original_target_position, play_by_play_lines)
            target.jump(game, original_flipflop_position, play_by_play_lines)

            play_by_play_lines.append(
                f"{self.name} ({self.piece}) swaps places with {target.name} ({target.piece}), jumping from {original_flipflop_position} to {original_target_position}."
            )

            self.skip_main_move = True
            self.register_ability_use(game, play_by_play_lines, description="FlipFlop")
        else:
            # Set the flag to False if no swap occurs, meaning the FlipFlop should roll normally
            self.skip_main_move = False