# critic.py

from .base_character import Character


class Critic(Character):
    """I can make any other racer reroll their main move once per turn.

    Simulator policy: "I can" is player choice. The sim invokes the reroll
    whenever another racer rolls at least `REROLL_THRESHOLD` (default 4) —
    a high-value roll that's worth disrupting, regardless of whether the
    rolling racer is ahead of or behind Critic. "Once per turn" means once
    per affected racer's main roll: the reroll_main_roll hook fires once
    per other-racer's roll, and we accept whatever the reroll produces
    (no chained second reroll like the old Buttinsky behavior).
    """

    POWER_PHASES = set()
    EDITION = "v2"

    REROLL_THRESHOLD = 4  # Force a reroll on rolls >= this value.

    def reroll_main_roll(self, roller, game, play_by_play_lines, roll):
        if roller is self:
            return roll
        if self.finished or self in game.eliminated_players:
            return roll
        if roll < self.REROLL_THRESHOLD:
            return roll

        play_by_play_lines.append(
            f"{self.name} ({self.piece}) doesn't approve — makes {roller.name} "
            f"({roller.piece}) reroll their {roll}."
        )
        new_roll = roller.main_roll(game, play_by_play_lines)
        self.register_ability_use(game, play_by_play_lines, description="Critic")
        return new_roll
