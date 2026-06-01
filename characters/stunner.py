# stunner.py

from .base_character import Character


class Stunner(Character):
    """Other racers within 1 space of me roll a 1 for all rolls.

    Not limited to the main move: any die a stunned racer rolls — Duelist
    duels, TheHose, Soulmate's soulmate-roll, Diceman's six dice,
    ShowOff's keep-rolling chain — comes up 1.

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

    Note: each override is an ability use — it credits the adjacent Stunner(s)
    with an ability activation AND triggers Scoocher (Scoocher reacts to any
    ability use, and a roll forced to 1 is an ability use). This can fire
    many times per turn (Diceman's 6 dice, ShowOff's chain) — that's
    intentional. Play-by-play prints a Stunner-forces line on each override
    so the cause is visible.
    """

    POWER_PHASES = set()
    EDITION = "v2"
