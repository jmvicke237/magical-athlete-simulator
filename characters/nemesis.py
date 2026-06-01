# nemesis.py

import random

from .base_character import Character
from power_system import PowerPhase


class Nemesis(Character):
    """Before my race, I pick any opposing racer. When I start my turn within
    5 spaces of them, I warp to their space.

    Implementation:
      - pick_nemesis is called once at race start (hooked from Game.run, same
        pattern as Mastermind.make_prediction). Picks a random non-self
        racer; the choice is made once per race and never re-picked.
      - pre_move_action (PRE_ROLL phase) checks |delta| to nemesis fresh
        each turn — nemesis's position changes constantly. Warps via
        self.jump() so board on_enter effects fire and on_another_player_jump
        notifications go out.

    Edge cases:
      - If nemesis has finished or been eliminated, no warp (skip).
      - If we're already sharing nemesis's space, no warp (no-op).
      - If Nemesis is alone (e.g. a 1-racer setup somehow), pick is skipped.

    Null interaction: pre_move_action is suppressed by the standard
    is_power_suppressed_for gate when Nemesis is ahead of an active Null,
    so the warp doesn't fire. The race-start pick happens before any
    movement, so suppression isn't a factor there.
    """

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    DEFAULT_WARP_RANGE = 5  # Default if Game.nemesis_warp_range isn't set.

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.nemesis = None
        self.has_picked_nemesis = False

    def pick_nemesis(self, game, play_by_play_lines):
        if self.has_picked_nemesis:
            return
        candidates = [p for p in game.players if p is not self]
        if not candidates:
            return
        self.nemesis = random.choice(candidates)
        self.has_picked_nemesis = True
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) picks {self.nemesis.name} ({self.nemesis.piece}) as their nemesis."
        )
        self.register_ability_use(game, play_by_play_lines, description="Nemesis pick")

    def pre_move_action(self, game, play_by_play_lines):
        if self.nemesis is None:
            return
        warp_range = getattr(game, "nemesis_warp_range", self.DEFAULT_WARP_RANGE)
        if warp_range <= 0:
            return  # Toggle off — race-start pick still happens, but warp never fires.
        if self.nemesis.finished or self.nemesis in game.eliminated_players:
            return
        if self.nemesis.position == self.position:
            return
        if abs(self.nemesis.position - self.position) > warp_range:
            return
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) is within {warp_range} of nemesis "
            f"{self.nemesis.name} ({self.nemesis.piece}) — warping to space {self.nemesis.position}."
        )
        self.jump(game, self.nemesis.position, play_by_play_lines)
        self.register_ability_use(game, play_by_play_lines, description="Nemesis warp")
