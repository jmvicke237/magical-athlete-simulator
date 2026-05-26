# stunner.py

from .base_character import Character


class Stunner(Character):
    """Other racers within 1 space of me roll a 1 for all rolls.

    Not limited to the main move: any die a stunned racer rolls — Duelist
    duels, SpitBall, Understudy's understudy-roll, Diceman's six dice,
    HighRoller's keep-rolling chain — comes up 1.

    Implementation: Game.roll_die() consults Game.is_near_stunner(player)
    on every die roll; if the rolling player is within 1 space of an
    active (non-Antimag-suppressed) Stunner, it returns 1 regardless of
    the underlying range. Per-character special rolls funnel through
    game.roll_die instead of bare random.randint to make the override
    universal.

    Antimag interaction: a Stunner strictly ahead of Antimag has their
    power suppressed (is_power_suppressed_for(Stunner) == True), and
    is_near_stunner ignores suppressed Stunners — so racers adjacent to
    a suppressed Stunner roll normally.

    Note: this is a passive proximity effect, not an "ability use" — it
    doesn't increment Stunner's ability_activations counter and doesn't
    trigger Scoocher per-override. Play-by-play prints a Stunner-forces
    line on each override so the cause is visible.
    """

    POWER_PHASES = set()
    EDITION = "v2"
