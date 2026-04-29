# buttinsky.py

from .base_character import Character

class Buttinsky(Character):
    """I make racers ahead of me reroll their main move if they roll 4 or more.
    Loops until the roll is below 4. Uses the same reroll_main_roll hook that
    Magician and Dicemonger use — fires once per main roll, before DIE_ROLL_TRIGGER.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    # Cap reroll attempts to handle deterministic rollers (e.g., Legs always
    # rolls 5, which would otherwise create an infinite loop with Buttinsky).
    # 5 attempts is plenty for normal d6 rerolls (P(<4 within 5)=96.9%).
    _MAX_REROLLS = 5

    def reroll_main_roll(self, roller, game, play_by_play_lines, roll):
        if roller is self:
            return roll
        if self.finished or self in game.eliminated_players:
            return roll
        if roller.position <= self.position:
            return roll  # Not ahead of me

        attempts = 0
        while roll >= 4 and attempts < self._MAX_REROLLS:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) butts in — makes {roller.name} "
                f"({roller.piece}) reroll their {roll}!"
            )
            roll = roller.main_roll(game, play_by_play_lines)
            self.register_ability_use(game, play_by_play_lines, description="Buttinsky")
            attempts += 1

        if attempts >= self._MAX_REROLLS and roll >= 4:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) gives up after {attempts} rerolls — "
                f"{roller.name}'s roll of {roll} stands."
            )
        return roll
