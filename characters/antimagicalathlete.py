# antimagicalathlete.py

from .base_character import Character

class AntimagicalAthlete(Character):
    """Racers ahead of me have no powers AND -1 to their main move.

    Suppression is dynamic — checked fresh at each power-firing call site,
    so it kicks in immediately as another racer passes me (e.g. NormalHarry's
    mid-pass elimination doesn't fire because by the time it would,
    NormalHarry is ahead and powerless).

    Implementation: Game.is_power_suppressed_for(character) is consulted at
    every "power" dispatch site:
      - resolve_phase / _execute_phase_action (all PRE_ROLL through POST_TURN)
      - base.move's on_being_passed, move_with_another, on_another_player_move
      - base.jump's on_another_player_jump
      - base.take_turn's reroll_main_roll and post_move_ability
      - NormalHarry's mid-pass elimination loop
      - Mole's _maybe_warp

    Main-move penalty: Game.get_antimag_main_move_penalty subtracts N spaces
    (default 1, the canonical rule) from the main-move of any racer ahead
    of Antimag. Applied in base.take_turn after the multiplier, clamped to
    0 (so a small roll just becomes a no-move, not backwards motion). The
    simulator's antimag_main_move_penalty toggle lets you tune this to a
    stronger value (-2, -3, …) for balance experiments; 0 disables it
    entirely if you ever want to test pure power-suppression behavior.

    Known limitations: characters with overridden main_roll (Diceman, Legs)
    still use their override even when ahead — main_roll dispatch isn't
    centralized through a hookable check. The penalty DOES still apply to
    those characters since it lives in take_turn after main_roll.
    """

    POWER_PHASES = set()
    EDITION = "v2"
