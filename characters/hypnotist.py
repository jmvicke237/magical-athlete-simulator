# hypnotist.py

from .base_character import Character
from power_system import PowerPhase

class Hypnotist(Character):
    """At the start of my turn, I can warp a racer to my space."""

    POWER_PHASES = {PowerPhase.PRE_ROLL}

    def pre_move_action(self, game, play_by_play_lines):
        """The Hypnotist warps the furthest player ahead of them to their space."""

        # Find the furthest player ahead (excluding MOUTH)
        furthest_player = None
        max_distance = 0
        for player in game.players:
            if not player.finished and player.position > self.position:
                distance = player.position - self.position
                if distance > max_distance:
                    max_distance = distance
                    furthest_player = player

        # Warp the furthest player if one is found
        if furthest_player and furthest_player.piece != "MOUTH":
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) hypnotizes {furthest_player.name} ({furthest_player.piece}) and warps them to their space!"
            )
            furthest_player.jump(game, self.position, play_by_play_lines)
            self.register_ability_use(game, play_by_play_lines, description="Hypnotist")