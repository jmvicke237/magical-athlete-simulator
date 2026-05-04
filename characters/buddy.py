# buddy.py

import random

from .base_character import Character
from power_system import PowerPhase


class Buddy(Character):
    """Before my race, I pick any other racer. Before my Main Move, if I am
    within 3 spaces of them, I warp to their space.

    Implementation:
      - pick_buddy is called once at race start (hooked from Game.run, same
        pattern as Mastermind.make_prediction). Picks a random non-self
        racer; the choice is made once per race and never re-picked.
      - pre_move_action (PRE_ROLL phase) checks |delta| to buddy fresh
        each turn — buddy's position changes constantly. Warps via
        self.jump() so board on_enter effects fire and on_another_player_jump
        notifications go out.

    Edge cases:
      - If buddy has finished or been eliminated, no warp (skip).
      - If we're already sharing buddy's space, no warp (no-op).
      - If Buddy is alone (e.g. a 1-racer setup somehow), pick is skipped.

    Antimag interaction: pre_move_action is suppressed by the standard
    is_power_suppressed_for gate when Buddy is ahead of an active Antimag,
    so the warp doesn't fire. The race-start pick happens before any
    movement, so suppression isn't a factor there.
    """

    POWER_PHASES = {PowerPhase.PRE_ROLL}
    EDITION = "v2"

    DEFAULT_WARP_RANGE = 3  # Default if Game.buddy_warp_range isn't set.

    def __init__(self, name, piece):
        super().__init__(name, piece)
        self.buddy = None
        self.has_picked_buddy = False

    def pick_buddy(self, game, play_by_play_lines):
        if self.has_picked_buddy:
            return
        candidates = [p for p in game.players if p is not self]
        if not candidates:
            return
        self.buddy = random.choice(candidates)
        self.has_picked_buddy = True
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) picks {self.buddy.name} ({self.buddy.piece}) as their buddy."
        )
        self.register_ability_use(game, play_by_play_lines, description="Buddy pick")

    def pre_move_action(self, game, play_by_play_lines):
        if self.buddy is None:
            return
        warp_range = getattr(game, "buddy_warp_range", self.DEFAULT_WARP_RANGE)
        if warp_range <= 0:
            return  # Toggle off — race-start pick still happens, but warp never fires.
        if self.buddy.finished or self.buddy in game.eliminated_players:
            return
        if self.buddy.position == self.position:
            return
        if abs(self.buddy.position - self.position) > warp_range:
            return
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) is within {warp_range} of buddy "
            f"{self.buddy.name} ({self.buddy.piece}) — warping to space {self.buddy.position}."
        )
        self.jump(game, self.buddy.position, play_by_play_lines)
        self.register_ability_use(game, play_by_play_lines, description="Buddy warp")
