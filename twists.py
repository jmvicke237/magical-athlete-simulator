# twists.py
#
# Twists board: just like Mild, except the first racer to reach position
# >= 14 (i.e., pass space 13) triggers a single randomly-drawn Twist that
# applies for the rest of the race. The full list of twist cards lives in
# `Updated Racers and Abilities - Sheet1.csv` paired with `Twists.csv`.
#
# Each twist is a function `apply_<name>(game, triggerer, play_by_play_lines)`
# that does the immediate effect AND seeds any persistent state (stored on
# game.twist_state). Persistent hooks live in game_simulation.py / base_character.py
# and consult game.twist_state to apply ongoing effects.

import random


# ---------------------------------------------------------------------------
# Registry — name → apply function. Order doesn't matter; selection is random.
# Swap Meet is intentionally not in the list (cup-level mechanic, can't be
# simulated within a single race).
# ---------------------------------------------------------------------------

def get_twist_pool():
    """Return the list of twist names eligible to be drawn. Mirror World,
    WEREMOUTH Containment Breach, and Season Finale are included — see their
    apply functions for the simulator-level implementation notes."""
    return [
        "Time Imp",
        "Curse Wands",
        "Conveyor Belt",
        "WEREMOUTH Containment Breach",
        "Mirror World",
        "Roast Chicken",
        "Bonkbug",
        "Randomness Ceased",
        "Season Finale",
        "Pinata",
        "No Running",
    ]


def draw_and_apply_twist(game, triggerer, play_by_play_lines, exclude=None):
    """Pick a random twist (excluding `exclude`) and apply it. Returns the
    name of the twist drawn."""
    pool = [t for t in get_twist_pool() if exclude is None or t not in exclude]
    if not pool:
        return None
    name = random.choice(pool)
    play_by_play_lines.append(f"!! TWIST DRAWN: {name} !!")
    APPLY_FUNCS[name](game, triggerer, play_by_play_lines)
    game.twists_drawn.append(name)
    return name


def apply_named_twist(game, triggerer, play_by_play_lines, name):
    """Force a specific twist by name (used when the simulator is configured
    to pin a particular twist instead of drawing randomly). Unknown names
    fall back to a random draw with a warning."""
    if name not in APPLY_FUNCS:
        play_by_play_lines.append(
            f"!! TWIST '{name}' unknown — falling back to random draw."
        )
        return draw_and_apply_twist(game, triggerer, play_by_play_lines)
    play_by_play_lines.append(f"!! TWIST (forced): {name} !!")
    APPLY_FUNCS[name](game, triggerer, play_by_play_lines)
    game.twists_drawn.append(name)
    return name


# ---------------------------------------------------------------------------
# Immediate / one-shot twists
# ---------------------------------------------------------------------------

def apply_time_imp(game, triggerer, lines):
    """The racer who triggered the twist is eliminated. The 'participates as
    an extra racer next race' part is cup-level (can't be simulated in a
    single race) — we just do the in-race elimination."""
    if triggerer is None:
        lines.append("  Time Imp: no triggerer recorded — nothing to eliminate.")
        return
    lines.append(
        f"  Time Imp stomped! {triggerer.name} ({triggerer.piece}) is eliminated."
    )
    game.eliminate_player(triggerer, lines)


def apply_roast_chicken(game, _triggerer, lines):
    """The last-place racer moves 7. One-shot — the bonus only applies on
    twist trigger, not for the rest of the race."""
    candidates = [
        p for p in game.players
        if not p.finished and p not in game.eliminated_players
    ]
    if not candidates:
        lines.append("  Roast Chicken: no eligible racers — fizzles.")
        return
    min_pos = min(p.position for p in candidates)
    last_pool = [p for p in candidates if p.position == min_pos]
    last = random.choice(last_pool)
    lines.append(
        f"  Roast Chicken: {last.name} ({last.piece}) (last place) moves 7."
    )
    last.move(game, lines, 7)


def apply_mirror_world(game, _triggerer, lines):
    """Reverse the race direction. Per spec: 'goal flips so you race back to
    0 AND rolls are reversed such that if you are on space 12 and roll a 3,
    you move to space 9' — and 'the player in last place is now in first'.

    Simulator implementation: mirror every active racer's position around
    the board midpoint (length/2). A racer at position N becomes
    `board.length - N`. After this one-time flip the rest of the race
    proceeds normally toward the original finish line (space 30) using
    normal roll-forward mechanics. This produces the SAME race-standings
    outcome as the literal rule (the last-place racer is now closest to the
    finish, and every roll still brings everyone closer to victory) without
    invasively rewriting every position-comparing character ability.

    Trade-off: the raw position NUMBERS players see in the play-by-play
    won't match a literal reading of the card (a racer who was on 12 ends
    up at 18 instead of staying at 12 with rolls negated), but the relative
    race outcome is equivalent.
    """
    active = [
        p for p in game.players
        if not p.finished and p not in game.eliminated_players
    ]
    if not active:
        lines.append("  Mirror World: no active racers — fizzles.")
        return
    lines.append(
        "  Mirror World: race direction reverses — every racer's position "
        "mirrors around the midpoint."
    )
    for p in active:
        old = p.position
        p.position = max(0, min(game.board.length - p.position, game.board.length))
        p.previous_position = p.position
        lines.append(
            f"    {p.name} ({p.piece}): {old} -> {p.position}"
        )

    # Edge case: any racer who was on the Start space (position 0) at the
    # time of the flip now lands exactly on the finish line (position N
    # mirrors to board.length - N = board.length). They auto-finish. We
    # resolve them in turn_order so 1st place (gold) goes to whoever comes
    # first in the turn order, then silver, then any remaining are just
    # "finished" with no chip. finish_player handles the chip awarding.
    for player_idx in game.turn_order:
        p = game.players[player_idx]
        if p.finished or p in game.eliminated_players:
            continue
        if p.position >= game.board.length:
            lines.append(
                f"    {p.name} ({p.piece}) was on the Start when mirrored — "
                f"now on the finish line, auto-finishes."
            )
            game.finish_player(p, lines)


# ---------------------------------------------------------------------------
# Persistent twists — set state on game.twist_state for ongoing hooks
# ---------------------------------------------------------------------------

def apply_conveyor_belt(game, _triggerer, lines):
    """Warp every active racer to space 1, then +3 to main move for the
    rest of the race. The +3 is applied in the ROLL_MODIFICATION-equivalent
    hook in base_character.take_turn."""
    active = [
        p for p in game.players
        if not p.finished and p not in game.eliminated_players
    ]
    if not active:
        lines.append("  Conveyor Belt: no active racers — fizzles.")
        return
    lines.append(
        "  Conveyor Belt activated: warping all racers to space 1, +3 main "
        "move for the rest of the race."
    )
    for p in active:
        old = p.position
        p.jump(game, 1, lines)
        if p.position != old:
            lines.append(
                f"    {p.name} ({p.piece}): {old} -> {p.position}"
            )
    game.twist_state["conveyor_bonus"] = 3


def apply_bonkbug(game, _triggerer, lines):
    """Last 2 spaces (length - 2 and length - 1 — i.e., 28 and 29 on a
    30-space board) become "move backwards 5" spaces when stopped on.
    Implemented by mutating the board's space list so the existing on_enter
    pipeline picks it up automatically."""
    from board import Space
    end = game.board.length
    affected = [end - 2, end - 1]
    lines.append(
        f"  Bonkbug infestation at the finish! Spaces {affected[0]} and "
        f"{affected[1]} now send racers backwards 5."
    )
    for idx in affected:
        if 0 <= idx < end:
            game.board.spaces[idx] = Space("move", value=-5)
    game.twist_state["bonkbug_active"] = True


def apply_pinata(game, _triggerer, lines):
    """Put a point chip on every empty space after the first corner
    (FIRST_CORNER_POSITION + 1 through board.length - 1). 'Empty' = the
    current space type is 'normal' (no portals, corners, trips, +/- spaces,
    etc.). Stopping on a chip space awards 1 bronze; the chip stays (no
    one-shot tracking — simpler to model as a permanent bronze-chip space)."""
    from board import Space
    from characters.nepobaby import FIRST_CORNER_POSITION
    placed = []
    for idx in range(FIRST_CORNER_POSITION + 1, game.board.length):
        space = game.board.spaces[idx]
        if space.space_type == "normal":
            game.board.spaces[idx] = Space("bronze_chip")
            placed.append(idx)
    lines.append(
        f"  Pinata leak: bronze chip placed on {len(placed)} empty space(s) "
        f"after the first corner (positions {placed[:5]}{'...' if len(placed) > 5 else ''})."
    )


def apply_no_running(game, _triggerer, lines):
    """Any racer whose final main-move distance is >= 6 is eliminated
    instead of moving. Checked in base_character.take_turn after roll mods
    but before the MOVEMENT phase."""
    lines.append(
        "  No Running by the scrying pool! Any racer who tries to main-move "
        "6+ spaces is eliminated."
    )
    game.twist_state["no_running_active"] = True


def apply_curse_wands(game, _triggerer, lines):
    """After each player's turn, that player rolls a die and the turn
    pointer advances by that many positions (skipping that many racers).
    Implemented as a hook in Game.run's per-turn loop that consults
    twist_state['curse_wands_active']."""
    lines.append(
        "  Curse Wands distributed! After each turn, the player rolls and "
        "we skip that many racers in turn order."
    )
    game.twist_state["curse_wands_active"] = True


def apply_randomness_ceased(game, _triggerer, lines):
    """Every active racer rolls one die NOW and that value is locked in for
    every future roll they make for the rest of the race. Implemented via
    a per-player override checked in Game.roll_die."""
    active = [
        p for p in game.players
        if not p.finished and p not in game.eliminated_players
    ]
    if not active:
        lines.append("  Randomness Ceased: no active racers — fizzles.")
        return
    lines.append("  Randomness has randomly ceased! Each racer rolls once for keeps:")
    fixed = {}
    for p in active:
        roll = random.randint(1, 6)  # bare random — bypasses Stunner override at trigger time
        fixed[id(p)] = roll
        lines.append(f"    {p.name} ({p.piece}): locked at {roll}")
    game.twist_state["fixed_rolls"] = fixed


def apply_weremouth_breach(game, _triggerer, lines):
    """Spawn a ghost W.E.R.E.M.O.U.T.H. at the Start. After every player's
    turn, the ghost rolls a die and moves that many spaces. Any racer it
    passes (started behind, ended ahead) is eliminated.

    The ghost is NOT a regular racer: it's not in `game.players` or
    `turn_order`, doesn't take its own turn, can't be triggered by other
    characters, and doesn't earn placement chips or points if it 'finishes'
    (it just stops moving when it reaches the finish line).

    Stored as a lightweight dict on game.twist_state['ghost_mouth']:
        { 'position': 0, 'name': 'Ghost WEREMOUTH' }
    The post-turn hook in Game.run rolls + moves it."""
    lines.append(
        "  Containment breach! A ghost W.E.R.E.M.O.U.T.H. has been placed "
        "at the Start. It rolls and moves after every turn, eliminating any "
        "racer it passes."
    )
    game.twist_state["ghost_mouth"] = {
        "position": 0,
        "name": "Ghost W.E.R.E.M.O.U.T.H.",
    }


def apply_season_finale(game, _triggerer, lines):
    """1st and 2nd place racers do a 1v1 at the second corner. Whoever
    finishes the 1v1 first gets gold + silver chips (both placement
    rewards, since they competed for all the points).

    Sim implementation: the 1v1 isn't a fresh race — we just place the top
    2 active racers (by position) at CORNER_POSITION, eliminate everyone
    else, and let the race continue. The first of the two to finish gets
    BOTH chips. This isn't a perfect mapping of 'race for all the points'
    but it captures the spirit (eliminate the pack, two racers sprint to
    the finish, winner takes both placement chips)."""
    from config import CORNER_POSITION
    active = [
        p for p in game.players
        if not p.finished and p not in game.eliminated_players
    ]
    if len(active) < 2:
        lines.append("  Season Finale: fewer than 2 active racers — fizzles.")
        return
    # Take the top 2 by current position; ties broken by turn order index.
    active.sort(key=lambda p: (-p.position, game.players.index(p)))
    finalists = active[:2]
    eliminated = active[2:]
    lines.append(
        f"  Season Finale! {finalists[0].name} ({finalists[0].piece}) vs "
        f"{finalists[1].name} ({finalists[1].piece}) — 1v1 at the second corner. "
        f"Winner takes gold AND silver."
    )
    # Position both at the second corner; eliminate everyone else.
    for f in finalists:
        old = f.position
        f.position = CORNER_POSITION
        f.previous_position = CORNER_POSITION
        lines.append(f"    {f.name} ({f.piece}): warped from {old} to {CORNER_POSITION}.")
    for e in eliminated:
        lines.append(
            f"    {e.name} ({e.piece}): not a finalist — eliminated from the race."
        )
        game.eliminate_player(e, lines)
    # Flag for finish_player to award double chips to the winner.
    game.twist_state["season_finale_active"] = True


# ---------------------------------------------------------------------------
# Apply-function registry
# ---------------------------------------------------------------------------

APPLY_FUNCS = {
    "Time Imp": apply_time_imp,
    "Curse Wands": apply_curse_wands,
    "Conveyor Belt": apply_conveyor_belt,
    "WEREMOUTH Containment Breach": apply_weremouth_breach,
    "Mirror World": apply_mirror_world,
    "Roast Chicken": apply_roast_chicken,
    "Bonkbug": apply_bonkbug,
    "Randomness Ceased": apply_randomness_ceased,
    "Season Finale": apply_season_finale,
    "Pinata": apply_pinata,
    "No Running": apply_no_running,
}
