# antimagicalathlete.py

from .base_character import Character

class AntimagicalAthlete(Character):
    """Racers ahead of me have no powers. Suppression is dynamic — checked
    fresh at each power-firing call site, so it kicks in immediately as
    another racer passes me (e.g. Weremouth's mid-pass elimination doesn't
    fire because by the time it would, Weremouth is ahead and powerless).

    Implementation: Game.is_power_suppressed_for(character) is consulted at
    every "power" dispatch site:
      - resolve_phase / _execute_phase_action (all PRE_ROLL through POST_TURN)
      - base.move's on_being_passed, move_with_another, on_another_player_move
      - base.jump's on_another_player_jump
      - base.take_turn's reroll_main_roll and post_move_ability
      - Weremouth's mid-pass elimination loop
      - Mole's _maybe_warp

    Optional simulator buff (off by default): Game.get_antimag_main_move_penalty
    additionally subtracts N spaces from the main-move of any racer ahead of
    Antimag. The penalty is configured via the antimag_main_move_penalty toggle
    in the Streamlit / Tkinter frontends and applied in base.take_turn after
    the multiplier, clamped to 0.

    Known limitations: characters with overridden main_roll (Diceman, Legs)
    still use their override even when ahead — main_roll dispatch isn't
    centralized through a hookable check. The penalty toggle DOES still apply
    to those characters since it lives in take_turn after main_roll.
    """

    POWER_PHASES = set()
    EDITION = "v2"
