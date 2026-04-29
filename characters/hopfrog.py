# hopfrog.py

from .base_character import Character

class Hopfrog(Character):
    """When I stop one space behind a racer, I get another turn.

    Triggers from post_move_ability — only fires after an actual main move
    (no trigger if tripped/clamped/no-movement). The bonus turn is queued via
    Game.queued_turns and runs after the current turn returns; chained bonuses
    process via the run loop's while-empty cleanup.
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def post_move_ability(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return
        # Require actual movement this turn — no new "stop" event without it.
        if self.position == self.turn_start_position:
            return

        target = self.position + 1
        if target > game.board.length:
            return  # Off the board, no racer can be there
        has_racer_one_ahead = any(
            p.position == target
            and p is not self
            and not p.finished
            and p not in game.eliminated_players
            for p in game.players
        )
        if not has_racer_one_ahead:
            return

        play_by_play_lines.append(
            f"{self.name} ({self.piece}) stopped one space behind a racer — gets another turn!"
        )
        self.register_ability_use(game, play_by_play_lines, description="Hopfrog")
        if not hasattr(game, 'queued_turns'):
            game.queued_turns = []
        game.queued_turns.append(self)
