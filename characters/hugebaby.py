# hugebaby.py

from .base_character import Character

class HugeBaby(Character):

    POWER_PHASES = set()

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        self._check_shared_space(game, play_by_play_lines)

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        self._check_shared_space(game, play_by_play_lines)

    def move(self, game, play_by_play_lines, spaces):
        super().move(game, play_by_play_lines, spaces)
        self._check_shared_space(game, play_by_play_lines)

    def jump(self, game, position, play_by_play_lines):
        super().jump(game, position, play_by_play_lines)
        self._check_shared_space(game, play_by_play_lines)
    
    def _check_shared_space(self, game, play_by_play_lines):
        """If any player is on HugeBaby's space, push them back one space.
        Skip the push if it would land them on a board space that would
        immediately return them to HugeBaby (preventing infinite loops, e.g.
        Wild board's "move +1" at position 11 with HugeBaby at 12)."""
        if self.position <= 0:
            return

        for other_player in game.players:
            if other_player == self or other_player.position != self.position:
                continue

            # Look ahead: would push-back land on a space that bounces them
            # right back to HugeBaby's position?
            target_pos = other_player.position - 1
            if 0 <= target_pos < game.board.length:
                target_space = game.board.spaces[target_pos]
                if target_space.space_type == "move":
                    landing = target_pos + target_space.value
                    if landing == self.position:
                        play_by_play_lines.append(
                            f"{other_player.name} ({other_player.piece}) is on "
                            f"{self.name} ({self.piece})'s space, but pushing "
                            f"to {target_pos} would loop them back — push skipped."
                        )
                        if other_player.piece != "Scoocher":
                            self.register_ability_use(game, play_by_play_lines, description="Hugebaby")
                        continue

            other_player.move(game, play_by_play_lines, -1)
            play_by_play_lines.append(
                f"{other_player.name} ({other_player.piece}) was pushed back by {self.name} ({self.piece})!"
            )
            if other_player.piece != "Scoocher":
                self.register_ability_use(game, play_by_play_lines, description="Hugebaby")
