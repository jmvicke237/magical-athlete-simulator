# hare.py

from .base_character import Character
from power_system import PowerPhase

class Hare(Character):
    """I get +2 to my main move. When I start my turn alone in the lead, I skip my move and get a bronze chip."""

    POWER_PHASES = {PowerPhase.PRE_ROLL, PowerPhase.ROLL_MODIFICATION}
    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.bronze_chips = 0 #this is placeholder since we haven't implemented points yet
    
    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Hare adds +2 to main move if not in lead."""
        if self.finished == True:
            return roll
        
        if other_player == self:
            modified_roll = roll + 2
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) gets +2 to their move. Move: {roll} -> {modified_roll}"
            )
            self.register_ability_use(game, play_by_play_lines, description="Hare")
            return modified_roll
        return roll

    def pre_move_action(self, game, play_by_play_lines):
        """Skips move if in lead (untied) and gets a bronze chip."""
        if self.is_lead_racer(game):
            self.skip_main_move = True
            self.bronze_chips += 1
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) skipped their move and received a bronze chip!"
            )
        else:
            self.skip_main_move = False

    def is_lead_racer(self, game):
        """Checks if the Hare is in the lead (strictly ahead of all other racers)."""
        for player in game.players:
            if player != self and not player.finished and player.position >= self.position:
                return False
        return True