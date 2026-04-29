# buttinsky.py

from .base_character import Character

class Buttinsky(Character):
    """I make racers ahead of me reroll their main move if they roll 4 or more.
    Loops until the roll is below 4. Uses the same reroll_main_roll hook that
    Magician and Dicemonger use — fires once per main roll, before DIE_ROLL_TRIGGER.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def reroll_main_roll(self, roller, game, play_by_play_lines, roll):
        if roller is self:
            return roll
        if self.finished or self in game.eliminated_players:
            return roll
        if roller.position <= self.position:
            return roll  # Not ahead of me

        while roll >= 4:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) butts in — makes {roller.name} "
                f"({roller.piece}) reroll their {roll}!"
            )
            roll = roller.main_roll(game, play_by_play_lines)
            self.register_ability_use(game, play_by_play_lines, description="Buttinsky")
        return roll
