# characters/centaur.py

from .base_character import Character

class Centaur(Character):
    """When I pass a racer, they move -2."""


    POWER_PHASES = set()
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def move(self, game, play_by_play_lines, spaces):
        # Record position before moving
        start_position = self.position

        # Compute this call's INTENDED end (clamped to the board) BEFORE
        # super().move runs. on_enter cascades inside super().move can
        # warp/push self.position past this point — Sportals portals
        # warp to the partner space, Wild +N/-N spaces push further.
        # Centaur should only push back racers passed by THIS main-move
        # segment; portal warps shouldn't trigger pass-keyword effects,
        # and Wild cascades fire their own Centaur.move recursively
        # (which handle their own segment's passes).
        intended_end = max(0, min(start_position + spaces, game.board.length))

        super().move(game, play_by_play_lines, spaces)

        if self.position == start_position:
            return  # blocked (Stickler) or no-op

        passed_racers = self.detect_passes(game, start_position, intended_end)

        # Apply Centaur's ability to each passed racer
        for player in passed_racers:
            if not player.finished:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) passed {player.name} ({player.piece}), moving them back 2 spaces."
                )
                player.move(game, play_by_play_lines, -2)
                self.register_ability_use(game, play_by_play_lines, description="Centaur")