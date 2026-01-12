# characters/alchemist.py

from .base_character import Character
from power_system import PowerPhase

class Alchemist(Character):
    """When I roll a 1 or 2 for my main move, I can move 4 instead."""

    POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.power_triggered = False    
    
    def take_turn(self, game, play_by_play_lines):
        self.turn_start_position = self.position
        self.last_roll = -1
        if self.tripped:
            self.tripped = False
            play_by_play_lines.append(f"{self.name} ({self.piece}) is tripped and skips their turn.")
            return
        self.pre_move_action(game, play_by_play_lines)
        if not self.skip_main_move:
            roll = self.main_roll(game, play_by_play_lines)
            self.last_roll = roll
            # Check for Dicemonger or other racer that allows for reroll of mainroll
            for player_index in game.turn_order:
                other_player = game.players[player_index]
                if hasattr(other_player, "reroll_main_roll"):
                    roll = other_player.reroll_main_roll(self, game, play_by_play_lines, roll)
            # Call trigger_on_main_move_roll on all other players *before* modifying the roll
            for player_index in game.turn_order:
                other_player = game.players[player_index]
                other_player.trigger_on_main_move_roll(self, game, self.last_roll, play_by_play_lines)
            if roll in (1,2):
                roll = 4
                self.register_ability_use(game, play_by_play_lines, description="Alchemist")
            if not self.skip_main_move:
                roll = self.modify_roll(game, play_by_play_lines, roll)
                self.move(game, play_by_play_lines, roll)
            if self.skip_main_move:
                self.skip_main_move = False
        self.post_move_ability(game, play_by_play_lines)