# doppelgangster.py

from .base_character import Character


class Doppelgangster(Character):
    """The racer who finishes 1st is eliminated instead. I get their power.

    Simulator implementation: Game.finish_player intercepts the FIRST racer
    to cross the finish line (provided it's not Doppelgangster themselves
    and Doppelgangster is still active). The would-be 1st-place racer is
    eliminated, and Doppelgangster's Python class is swapped into the
    eliminated racer's class via `instance.__class__ = TargetClass`.
    Doppelgangster keeps their existing position, chips, and base state
    but immediately starts using the target class's POWER_PHASES, methods,
    and __init__-set instance attrs (NormalHarry's is_transformed flag,
    Nemesis's pick state, Penguin's recovery flag, etc.).

    Caveat: the piece-name string stays "Doppelgangster" after the swap.
    Character logic that uses class-based dispatch / POWER_PHASES (the
    majority) works correctly post-swap; logic that checks the piece
    name directly (e.g., Stunner's `p.piece == "Stunner"` proximity
    check) won't recognize a transformed Doppelgangster as the new
    class. Stat tracking continues to attribute everything to the
    Doppelgangster piece for clarity.

    Edge cases:
      - If Doppelgangster IS the first finisher, no intercept (we don't
        self-eliminate). Doppelgangster gets the gold chip normally.
      - If Doppelgangster is already finished or eliminated when the
        first finisher crosses, no intercept.
      - After the swap fires once, Doppelgangster's class has changed,
        so any second finisher in the same race proceeds normally.
      - Class-swap to Doppelgangster (would only happen if a second
        Doppelgangster were the would-be finisher, which can't actually
        occur — the first to finish IS the one being intercepted) is
        explicitly skipped to avoid no-op self-swaps.
    """

    POWER_PHASES = set()
    EDITION = "v2"
