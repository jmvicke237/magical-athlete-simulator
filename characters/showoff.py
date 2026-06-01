# showoff.py

from .base_character import Character

class ShowOff(Character):
    """After I roll for my main move, I can keep rolling and adding each
    amount to my move. If I ever roll the same or lower, I don't move.

    Simulator policy: ShowOff chooses when to stop pressing their luck
    using the game.showoff_threshold knob (default 5). They keep rolling
    while the running total is below the threshold, and stop once they meet
    or exceed it. Higher threshold = greedier = more bust risk. Bust here
    means "no movement this turn" — there's no trip carry-over to next turn.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def main_roll(self, game, play_by_play_lines):
        # Antimag: ShowOff's override is a power. Fall back to base d6 if suppressed.
        if game.is_power_suppressed_for(self):
            return Character.main_roll(self, game, play_by_play_lines)

        threshold = getattr(game, 'showoff_threshold', 5)
        last_roll = None
        total = 0
        first_log = True

        while True:
            new_roll = game.roll_die(self, play_by_play_lines)
            # PartyPooper hook on this individual die
            while new_roll == 6 and self._trigger_party_pooper(game, play_by_play_lines):
                new_roll = game.roll_die(self, play_by_play_lines)

            busted = last_roll is not None and new_roll <= last_roll

            if first_log:
                play_by_play_lines.append(
                    f"{self.name} ({self.piece}) rolls {new_roll} (target ≥{threshold})"
                )
                first_log = False
            elif busted:
                play_by_play_lines.append(
                    f"  {self.name} rolls again: {new_roll} — busted (≤ previous {last_roll})"
                )
            else:
                play_by_play_lines.append(
                    f"  {self.name} rolls again: {new_roll} (running total: {total + new_roll})"
                )

            if busted:
                play_by_play_lines.append(
                    f"  ShowOff busts and doesn't move this turn!"
                )
                self.skip_main_move = True
                self.last_roll = 0
                self.register_ability_use(game, play_by_play_lines, description="ShowOff busted")
                return 0

            total += new_roll
            last_roll = new_roll

            if total >= threshold:
                break

        play_by_play_lines.append(
            f"  ShowOff hit target — moves {total}"
        )
        self.last_roll = total
        self.register_ability_use(game, play_by_play_lines, description="ShowOff")
        return total
