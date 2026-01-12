# characters/cheerleader.py

from .base_character import Character

class Cheerleader(Character):
    def __init__(self, name, piece):
        super().__init__(name, piece)

    def pre_move_action(self, game, play_by_play_lines):
        """Cheerleader moves last place player(s) forward 2, and self 1."""

        min_position = min([p.position for p in game.players if not p.finished and p not in game.eliminated_players], default=float('inf'))

        last_place_players = [
            player for player in game.players
            if player.position == min_position and not player.finished
        ]
    
        for player in last_place_players:
            player.move(game, play_by_play_lines, 2) # Move all last place players, including possibly the cheerleader

        # Move +1 *if* any last place players were moved (including self)
        if len(last_place_players) > 0: #Simplified check.
            self.move(game, play_by_play_lines, 1)
            play_by_play_lines.append(f"{self.name} ({self.piece}) moved forward 1 (Cheerleader ability).")
            self.register_ability_use(game, play_by_play_lines, description="Cheerleader")