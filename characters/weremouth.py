# weremouth.py

from .base_character import Character
from power_system import PowerPhase

class Weremouth(Character):
    """When I roll a 1 or 2 for my main move, I transform into a W.E.R.E.M.O.U.T.H.
    for the rest of the race and eliminate any racers I pass. Transformation happens
    before the move, so eliminations apply on the transformation turn too."""

    POWER_PHASES = {PowerPhase.DIE_ROLL_TRIGGER}
    EDITION = "v2"

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.is_transformed = False

    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        if roller is self and not self.is_transformed and roll in (1, 2) and not self.finished:
            self.is_transformed = True
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) rolled a {roll} and transforms into a W.E.R.E.M.O.U.T.H.!"
            )
            self.register_ability_use(game, play_by_play_lines, description="Weremouth transformed")

    def move(self, game, play_by_play_lines, spaces):
        if not self.is_transformed or spaces <= 0 or self.finished:
            super().move(game, play_by_play_lines, spaces)
            return

        start_pos = self.position
        # Compute this call's INTENDED end (clamped to the board) BEFORE
        # super().move runs. on_enter cascades inside super().move can
        # change self.position past this point — Sportals portals warp
        # to the partner space, Wild +N/-N spaces push further. We only
        # want to eat racers passed by THIS main-move segment; portal
        # warps shouldn't trigger pass-keyword eating per the warp rule,
        # and Wild cascades fire their own Weremouth.move recursively
        # (which handle their own eating range).
        intended_end = max(0, min(start_pos + spaces, game.board.length))

        # Snapshot positions of racers ahead of us BEFORE moving — their positions
        # may shift during super().move() via on_being_passed reactions.
        candidates = [
            (p, p.position) for p in game.players
            if p is not self and not p.finished
            and p not in game.eliminated_players
            and p.position > start_pos
        ]

        super().move(game, play_by_play_lines, spaces)

        if self.position == start_pos:
            return  # blocked (Stickler) or no-op

        for player, original_pos in candidates:
            # AntimagicalAthlete: if Weremouth's pass put us ahead of Antimag,
            # Weremouth's powers are suppressed mid-pass, so no eliminations.
            if game.is_power_suppressed_for(self):
                break
            if (start_pos < original_pos < intended_end
                    and not player.finished
                    and player not in game.eliminated_players):
                game.eliminate_player(player, play_by_play_lines)
                self.register_ability_use(
                    game, play_by_play_lines,
                    description=f"Weremouth ate {player.piece}"
                )
