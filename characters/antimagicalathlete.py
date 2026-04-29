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

    Known limitations: characters with overridden main_roll (Diceman, Legs)
    still use their override even when ahead — main_roll dispatch isn't
    centralized through a hookable check.
    """

    POWER_PHASES = set()
    EDITION = "v2"
