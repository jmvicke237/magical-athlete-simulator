# characters/copycat.py

from .base_character import Character
from power_system import PowerPhase

class Copycat(Character):
    """I have the power of the racer currently in the lead. If there's a tie, I pick."""

    # Copycat participates in all phases to dynamically copy whoever is in the lead
    POWER_PHASES = {
        PowerPhase.PRE_ROLL,
        PowerPhase.DIE_ROLL_TRIGGER,
        PowerPhase.ROLL_MODIFICATION,
        PowerPhase.POST_TURN
    }

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.copied_character = None

    def get_lead_racer(self, game):
        """Find the racer currently in the lead (closest to finish line)."""
        max_position = -1
        lead_racers = []

        for player in game.players:
            if player != self and not player.finished:
                if player.position > max_position:
                    max_position = player.position
                    lead_racers = [player]
                elif player.position == max_position:
                    lead_racers.append(player)

        # If tie, pick the first one (simplified AI choice)
        return lead_racers[0] if lead_racers else None

    def _copy_ability(self, game, method_name, *args, **kwargs):
        """Call the copied character's method if they have it."""
        lead = self.get_lead_racer(game)

        if lead and hasattr(lead, method_name):
            method = getattr(lead, method_name)
            # Call the method with self as the first argument (mimicking the lead's behavior)
            return method(*args, **kwargs)

        return None

    # Override key methods to delegate to copied character
    def pre_move_action(self, game, play_by_play_lines):
        """Copy lead racer's pre_move_action."""
        lead = self.get_lead_racer(game)
        if lead and PowerPhase.PRE_ROLL in getattr(lead.__class__, 'POWER_PHASES', set()):
            # Temporarily swap identities
            temp_self = self
            self.__class__ = lead.__class__
            try:
                self.__class__.pre_move_action(temp_self, game, play_by_play_lines)
            finally:
                self.__class__ = Copycat

    def modify_other_roll(self, other_player, game, play_by_play_lines, roll):
        """Copy lead racer's roll modification."""
        if other_player != self:
            return roll  # Only modify our own rolls

        lead = self.get_lead_racer(game)
        if lead and PowerPhase.ROLL_MODIFICATION in getattr(lead.__class__, 'POWER_PHASES', set()):
            # Check if lead has the method
            if hasattr(lead, 'modify_other_roll'):
                # Call it as if we are modifying our own roll
                return lead.modify_other_roll(self, game, play_by_play_lines, roll)
        return roll

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        """Copy lead racer's roll trigger."""
        lead = self.get_lead_racer(game)
        if lead and PowerPhase.DIE_ROLL_TRIGGER in getattr(lead.__class__, 'POWER_PHASES', set()):
            if hasattr(lead, 'trigger_on_main_move_roll'):
                lead.trigger_on_main_move_roll(roller, game, roll, play_by_play_lines)

    def post_turn_actions(self, game, other_player, play_by_play_lines):
        """Copy lead racer's post-turn actions."""
        lead = self.get_lead_racer(game)
        if lead and PowerPhase.POST_TURN in getattr(lead.__class__, 'POWER_PHASES', set()):
            if hasattr(lead, 'post_turn_actions'):
                lead.post_turn_actions(game, other_player, play_by_play_lines)

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        """Copy lead racer's reaction to other player moves."""
        lead = self.get_lead_racer(game)
        if lead and hasattr(lead, 'on_another_player_move'):
            lead.on_another_player_move(moved_player, game, play_by_play_lines)
