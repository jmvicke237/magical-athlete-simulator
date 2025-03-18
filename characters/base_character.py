# characters/base_character.py
import random

class Character:
    def __init__(self, name, piece):
        self.name = name
        self.piece = piece
        self.position = 0
        self.previous_position = 0
        self.finished = False
        self.eliminated = False
        self.tripped = False
        self.turn_start_position = 0
        self.last_roll = -1
        self.skip_main_move = False

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
            self.last_roll = roll
            # Call trigger_on_main_move_roll on all other players *before* modifying the roll
            for player_index in game.turn_order:
                other_player = game.players[player_index]
                other_player.trigger_on_main_move_roll(self, game, self.last_roll, play_by_play_lines)
            if not self.skip_main_move:
                roll = self.modify_roll(game, play_by_play_lines, roll)
                self.move(game, play_by_play_lines, roll)
            if self.skip_main_move:
                self.skip_main_move = False
        self.post_move_ability(game, play_by_play_lines)

    def pre_move_action(self, game, play_by_play_lines):
        pass

    def main_roll(self, game, play_by_play_lines):
        roll = random.randint(1, 6)
        play_by_play_lines.append(f"{self.name} ({self.piece}) rolled a {roll}")
        self.last_roll = roll
        return roll
    
    def modify_roll(self, game, play_by_play_lines, roll):
        """Iterate through all *other* players in turn order and apply their modifications."""
        for player_index in game.turn_order:
            other_player = game.players[player_index]
            if hasattr(other_player, "modify_other_roll"):
                roll = other_player.modify_other_roll(self, game, play_by_play_lines, roll)
        return roll
    
    def move(self, game, play_by_play_lines, spaces): # IF CHANGED ALSO CHANGE LEAPTOAD
        if self.finished:
            return

        self.previous_position = self.position
        self.position = min(self.position + spaces, game.board.length)

        if self.position >= game.board.length:
            self.position = game.board.length
            game.finish_player(self, play_by_play_lines)
            play_by_play_lines.append(f"{self.name} ({self.piece}) moved from {self.previous_position} to {self.position} and finished!")
        else:
            play_by_play_lines.append(f"{self.name} ({self.piece}) moved from {self.previous_position} to {self.position}")

        # Move Suckerfish before checking for on another_player_move to avoid conflicts with Romantic etc
        for p in game.players:
            if p.piece == "Suckerfish":
                p.move_with_another(self, spaces, game, play_by_play_lines)
        
        for other_player in game.players:
            if other_player != self:
                other_player.on_another_player_move(self, game, play_by_play_lines)

    def post_move_ability(self, game, play_by_play_lines):
        pass

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        pass

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        pass

    def trip(self, game, play_by_play_lines):
        self.tripped = True

    def jump(self, game, position, play_by_play_lines):
        self.previous_position = self.position
        self.position = position

        if self.position >= game.board.length:
            self.position = game.board.length
            game.finish_player(self, play_by_play_lines)
            play_by_play_lines.append(f"{self.name} ({self.piece}) jumped from {self.previous_position} to {self.position} and finished!")
        else:
            play_by_play_lines.append(f"{self.name} ({self.piece}) jumped from {self.previous_position} to {self.position}")

        for other_player in game.players:
            if other_player != self:
                other_player.on_another_player_jump(self, game, play_by_play_lines)

    def check_for_share_space(self, game):
        space_mates = []
        for other_player in game.players:
            if other_player != self and other_player.position == self.position and not other_player.finished:
                space_mates.append(other_player)
        return space_mates
    
    def post_turn_actions(self, game, other_player, play_by_play_lines):
        pass
    
    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        """Called immediately after a player's main roll, before modifications."""
        pass