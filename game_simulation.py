# game_simulation.py
import random
from config import character_abilities, BOARD_LENGTH, MAX_TURNS, CORNER_POSITION, BOARD_TYPES, DEFAULT_BOARD_TYPE
from characters.base_character import Character
from board import Board
from power_system import PowerPhase
from debug_utils import TurnEventCapExceeded

class Game:
    def __init__(self, character_names, board_type=DEFAULT_BOARD_TYPE, board=None, random_turn_order=False, speeddemon_threshold=4, speeddemon_starting_points=3, speeddemon_check_timing="start", showoff_threshold=5, random_starting_bronze=True, null_main_move_penalty=1, spoilsport_threshold=5, nemesis_warp_range=5, random_board_pool=None, cheatah_alt_mode=True, forced_twist=None):
        self.players = []
        self.speeddemon_threshold = speeddemon_threshold  # Lead size that triggers SpeedDemon self-elimination (strict > comparison)
        self.speeddemon_check_timing = speeddemon_check_timing  # "start" or "end" — when the elimination check fires
        self._speeddemon_starting_points = speeddemon_starting_points  # Granted as bronze chips after player creation
        self.showoff_threshold = showoff_threshold  # ShowOff stops rolling once total >= this
        self._random_starting_bronze = random_starting_bronze  # Each racer gets random 0-5 starting bronze chips
        self._null_main_move_penalty = max(0, int(null_main_move_penalty))  # Subtracted from the main-move spaces of any racer strictly ahead of an active Null. Canonical rule is 1 (the -1 is part of Null's power); 0 disables it entirely for testing.
        self.spoilsport_threshold = max(1, int(spoilsport_threshold))  # Minimum lead (in spaces) every other racer must have over Spoilsport before they cancel the race.
        self.nemesis_warp_range = max(0, int(nemesis_warp_range))  # Max distance (inclusive) between Nemesis and their picked target that lets the pre-move warp fire; 0 disables the warp.
        self.cheatah_alt_mode = bool(cheatah_alt_mode)  # When True (default), both Cheatah and the guesser pick from 4-6 only (1-in-3 hit rate, higher movement floor). When False, both pick from 1-6 (1-in-6 hit rate, full range).
        
        # Handle board creation
        if board:
            self.board = board
        else:
            # If board_type is Random, pick from random_board_pool (default
            # ["Mild", "Wild"] for backward compat — Sportals must be
            # explicitly included by the caller).
            actual_board_type = board_type
            if board_type == "Random":
                pool = random_board_pool or ["Mild", "Wild"]
                actual_board_type = random.choice(list(pool))

            self.board = Board(board_type=actual_board_type, corner_position=CORNER_POSITION)
        
        self.finished_players = []
        self.eliminated_players = []
        self.turn_order = []
        self.current_player_index = 0
        self.race_cancelled = False  # Set by Spoilsport (or similar) to end the race
        # Watchdog: counts move/jump/ability events per turn. Reset in _take_turn_or_stun.
        # Exceeding the cap raises TurnEventCapExceeded to abort the runaway cascade.
        self._turn_event_count = 0
        self._turn_event_cap = 5000
        self._current_turn = 0  # Tracked for diagnostic logging
        self._watchdog_diagnostics = []  # Diagnostic strings for any aborted turns this race
        
        # Recursion tracking for different operations
        self._recursion_depths = {
            'scoocher': 0,
            'movement': 0,
            'ability': 0,
            'space_check': 0
        }
        self._max_recursion_depth = 3  # Original conservative cap. Fan-out via on_another_player_move means each level multiplies events; deeper caps blow memory on V1+V2 Wild races. State-loop detection in move/jump is the primary cycle protection.

        # State history for detecting true infinite loops (repeating game states)
        self._state_history = []

        # Twists board state. `twist_triggered` flips True the first time a
        # racer crosses past space 13 on a Twists board, at which point a
        # twist is drawn and applied. `twists_drawn` is the list of drawn
        # twists (typically one entry). `twist_state` is a bag of per-twist
        # persistent data — keys consumed by hooks below (conveyor_bonus,
        # no_running_active, curse_wands_active, fixed_rolls, ghost_mouth,
        # season_finale_active, bonkbug_active).
        self.twist_triggered = False
        self.twists_drawn = []
        self.twist_state = {}
        # Forced twist: None or "All" → draw randomly from the pool;
        # otherwise pin to the named twist (must match an entry in
        # twists.APPLY_FUNCS, else falls back to random with a warning).
        self.forced_twist = forced_twist if forced_twist and forced_twist != "All" else None
        
        self._create_players(character_names, random_turn_order)

        # Snapshot baseline as ALL ZEROS for character-spec chips (e.g.,
        # Sisyphus starts with 4 bronze in __init__ — those are part of the
        # character's mechanic and DO count as "points earned this race", so
        # we don't include them in the baseline).
        self._chip_baseline = {
            id(p): (0, 0, 0) for p in self.players
        }

        # Random starting bronze chips per racer (0-5 each). These DO go into
        # the baseline (settings-based chips don't count as earned points).
        if self._random_starting_bronze:
            for player in self.players:
                bonus = random.randint(0, 5)
                player.bronze_chips += bonus
                g, s, b = self._chip_baseline[id(player)]
                self._chip_baseline[id(player)] = (g, s, b + bonus)

        # Grant SpeedDemon starting bronze chips (overrides everything for
        # SpeedDemon — including any natural chips and any random bonus).
        # Baseline updated to match so delta starts at 0.
        if self._speeddemon_starting_points > 0:
            for player in self.players:
                if player.piece == "SpeedDemon":
                    player.bronze_chips = self._speeddemon_starting_points
                    g, s, _ = self._chip_baseline[id(player)]
                    self._chip_baseline[id(player)] = (g, s, self._speeddemon_starting_points)

    def _create_players(self, character_names, random_turn_order):
        for i, name in enumerate(character_names):
            char_class = character_abilities.get(name, Character)
            # Use piece name directly, and a default player name.
            player = char_class(name=f"Player {i+1}", piece=name)
            self.players.append(player)
            self.turn_order.append(i)
        if random_turn_order:
            random.shuffle(self.turn_order)
        for i, player in enumerate(self.players):
            player.player_number = i + 1

    def get_game_state_snapshot(self):
        """Get a hashable snapshot of current game state for loop detection.

        Returns a tuple representing the complete game state. If this state
        repeats, we have a true infinite loop.
        """
        return (
            tuple(p.position for p in self.players),
            tuple(p.finished for p in self.players),
            tuple(p.tripped for p in self.players),
            tuple(p.skip_main_move for p in self.players),
        )

    def check_for_state_loop(self, character_name, play_by_play_lines):
        """Check if the current game state has been seen before in this turn.

        Returns True if a loop is detected (same state seen twice).
        This indicates a true infinite loop that should be broken.

        NOTE: This also adds the current state to history, so states persist
        across ability-triggered moves within a turn.
        """
        current_state = self.get_game_state_snapshot()

        if current_state in self._state_history:
            # We've returned to a previous state - this is a true infinite loop!
            play_by_play_lines.append(
                f"Infinite loop detected: Game returned to identical state. Breaking loop for {character_name}."
            )
            return True

        # Add current state to history for future loop detection
        self._state_history.append(current_state)
        return False

    def clear_state_history(self):
        """Clear state history at the end of a turn."""
        self._state_history = []

    def push_game_state(self):
        """Push current game state onto history stack."""
        self._state_history.append(self.get_game_state_snapshot())

    def pop_game_state(self):
        """Pop most recent game state from history stack."""
        if self._state_history:
            self._state_history.pop()

    def run(self, play_by_play_lines):
        turns = 0
        
        for player in self.players:
            player.ability_activations = 0
        
        for player in self.players:
            if player.piece == "Mastermind":
                player.make_prediction(self, play_by_play_lines)
            elif player.piece == "Nemesis":
                player.pick_nemesis(self, play_by_play_lines)

        while not self.should_game_end(play_by_play_lines) and turns < MAX_TURNS:
            turns += 1
            self._current_turn = turns  # for watchdog diagnostics
            play_by_play_lines.append(f"\nTurn {turns}:")

            for _ in range(len(self.players)):
                player = self.current_player
                if not player.finished and player not in self.eliminated_players:
                    self._take_turn_or_stun(player, play_by_play_lines)
                    if self.should_game_end(play_by_play_lines):
                        break
                    # Note: post_turn_actions is now handled by POST_TURN phase in take_turn()

                    # Check for queued turns (e.g., Skipper, Hopfrog).
                    # Single-round only: chained bonus turns that re-add to
                    # the queue inside their own take_turn will be picked up
                    # on the NEXT outer-loop iteration. Avoids unbounded
                    # cascades on V1+V2 Wild combos (Hopfrog + Romantic + Mole
                    # ping-ponging fan-out).
                    if hasattr(self, 'queued_turns') and self.queued_turns:
                        queued_players = self.queued_turns[:]
                        self.queued_turns = []

                        for queued_player in queued_players:
                            if not queued_player.finished and queued_player not in self.eliminated_players:
                                self._take_turn_or_stun(queued_player, play_by_play_lines)
                                # Set current player to queued player so next_player() advances from here
                                self.current_player_index = self.players.index(queued_player)
                                if self.should_game_end(play_by_play_lines):
                                    break
                        if self.should_game_end(play_by_play_lines):
                            break

                    # Twists: after-turn hooks. Both fire only on Twists
                    # boards once the twist has actually triggered.
                    self._post_turn_twist_hooks(player, play_by_play_lines)
                    if self.should_game_end(play_by_play_lines):
                        break

                if self.should_game_end(play_by_play_lines):
                    break
                self.next_player()

        # Auto-finish the last surviving racer when the race ended due to
        # elimination (everyone else eaten by NormalHarry/MOUTH/Kraken etc.).
        # In a real game they'd just roll until they reach the finish, so
        # they get whichever placement slot is still open: gold if no one
        # finished, silver if one racer had already finished. Skipped on
        # Spoilsport cancellation (race_cancelled) and MAX_TURNS timeout —
        # those endings aren't "I won the remaining slot," they're a wash.
        if not getattr(self, 'race_cancelled', False) and turns < MAX_TURNS:
            survivors = [
                p for p in self.players
                if not p.finished and p not in self.eliminated_players
            ]
            if len(survivors) == 1:
                survivor = survivors[0]
                play_by_play_lines.append(
                    f"{survivor.name} ({survivor.piece}) is the last racer "
                    f"standing — auto-finishes the race."
                )
                self.finish_player(survivor, play_by_play_lines)

        # End-of-race hooks (e.g., Gloth's no-corner bonus). Null
        # suppression applies — racers ahead of Null don't get end-of-race powers.
        for player in self.players:
            if not self.is_power_suppressed_for(player):
                player.on_race_end(self, play_by_play_lines)

        play_by_play_lines.append("The race has ended!")
        play_by_play_lines.append(f"Total Turns: {turns:02d}")

        play_by_play_lines.append("\nAbility Activation Summary:")
        for player in self.players:
            play_by_play_lines.append(f"{player.name} ({player.piece}): {player.ability_activations} ability uses")
            
        play_by_play_lines.append("\nChip Summary:")
        for player in self.players:
            points = (player.gold_chips * 5) + (player.silver_chips * 3) + (player.bronze_chips * 1)
            play_by_play_lines.append(f"{player.name} ({player.piece}): {points} points (Gold: {player.gold_chips}, Silver: {player.silver_chips}, Bronze: {player.bronze_chips})")
        
        final_placements = self.assign_final_placements()
        for place, placed_player in final_placements:
            play_by_play_lines.append(f"{place}: {placed_player.name} ({placed_player.piece})")
        return turns, final_placements

    def is_power_suppressed_for(self, character):
        """True if any active Null is in the game and the given
        character is strictly ahead of them. Null's spec:
        "Racers ahead of me have no powers." Position is checked dynamically
        at each call site so suppression updates immediately as racers move."""
        for p in self.players:
            if (p.piece == "Null"
                    and p is not character
                    and not p.finished
                    and p not in self.eliminated_players
                    and character.position > p.position):
                return True
        return False

    def get_null_main_move_penalty(self, character):
        """Magnitude (>=0) to subtract from the given character's main-move
        spaces when they are strictly ahead of any active Null.
        Canonical penalty is 1 — part of Null's power along with power
        suppression. Returns 0 if the penalty is disabled (toggle set to 0),
        no Null is active, or the character isn't ahead. Reuses
        is_power_suppressed_for for the position check so the penalty
        stays in lockstep with power suppression."""
        if self._null_main_move_penalty <= 0:
            return 0
        if self.is_power_suppressed_for(character):
            return self._null_main_move_penalty
        return 0

    def _take_turn_or_stun(self, player, play_by_play_lines):
        """Run the player's turn inside a watchdog so a runaway character
        cascade can't grow unbounded. The Stunner proximity check used to
        live here as a turn-skip gate; under the new Stunner rule it
        moved to Game.roll_die (per-roll override) so adjacent racers
        still take their turn but every die they roll comes up 1."""
        # Reset event counter BEFORE any logic in this function. Otherwise
        # a high leftover count from a previous aborted turn would
        # re-trip the watchdog before we get to the try-block.
        self._turn_event_count = 0

        try:
            player.take_turn(game=self, play_by_play_lines=play_by_play_lines)
        except TurnEventCapExceeded as exc:
            chars = [p.piece for p in self.players]
            positions = [(p.piece, p.position) for p in self.players]
            diag = (
                f"WATCHDOG: turn {self._current_turn} aborted for "
                f"{player.name} ({player.piece}) — {self._turn_event_count} events "
                f"(cap {self._turn_event_cap}). chars={chars}, positions={positions}"
            )
            play_by_play_lines.append(diag)
            self._watchdog_diagnostics.append(diag)
            # Surface to terminal so the user sees it during a hung sim
            print(diag, flush=True)
            # Reset count so subsequent turns start fresh.
            self._turn_event_count = 0

    def _post_turn_twist_hooks(self, current_player, play_by_play_lines):
        """Twists board: ongoing per-turn effects. Called after every
        player's turn (and any queued bonus turns)."""
        if not self.twist_triggered:
            return

        # WEREMOUTH Containment Breach: ghost WEREMOUTH rolls and moves,
        # eliminating any active racer it passes (started behind, ended
        # at-or-ahead). Stops moving once it hits the finish line. Doesn't
        # take turns of its own and doesn't earn placement chips.
        ghost = self.twist_state.get('ghost_mouth')
        if ghost is not None and ghost['position'] < self.board.length:
            roll = random.randint(1, 6)
            start = ghost['position']
            end = min(start + roll, self.board.length)
            play_by_play_lines.append(
                f"  Ghost W.E.R.E.M.O.U.T.H. rolls {roll} and moves from "
                f"{start} to {end}."
            )
            for p in self.players:
                if p.finished or p in self.eliminated_players:
                    continue
                # Pass detection: ghost crossed past this racer's space.
                # If the ghost lands ON the racer, also eat them (sharing
                # a space with a transformed WEREMOUTH = consumed).
                if start <= p.position <= end:
                    play_by_play_lines.append(
                        f"    Ghost W.E.R.E.M.O.U.T.H. devours {p.name} ({p.piece})!"
                    )
                    self.eliminate_player(p, play_by_play_lines)
            ghost['position'] = end

        # Curse Wands: the player who just finished their turn rolls, and
        # the turn pointer advances by that many slots (skipping racers).
        if self.twist_state.get('curse_wands_active'):
            roll = random.randint(1, 6)
            play_by_play_lines.append(
                f"  Curse Wands: {current_player.name} ({current_player.piece}) "
                f"rolls {roll} — skipping {roll} racer(s) in turn order."
            )
            for _ in range(roll):
                self.next_player()

    def maybe_trigger_twist(self, mover, play_by_play_lines):
        """Twists board hook. Called after every position change. The first
        racer whose position reaches >= 14 (i.e., passes space 13) triggers
        a single randomly-drawn twist that applies for the rest of the race.
        No-op on non-Twists boards or after the twist has already fired."""
        if self.twist_triggered:
            return
        if getattr(self.board, "board_type", None) != "Twists":
            return
        # Check ALL active racers — the trigger fires for whoever first
        # crosses the threshold, which may not be `mover` (e.g., a HugeBaby
        # push could send someone else past 13).
        crossed = [
            p for p in self.players
            if not p.finished
            and p not in self.eliminated_players
            and p.position >= 14
        ]
        if not crossed:
            return
        # Prefer `mover` as the triggerer if they're among the crossed set
        # (matches the intuitive "I rolled and passed space 13"); otherwise
        # pick whoever's furthest along.
        if mover is not None and mover in crossed:
            triggerer = mover
        else:
            triggerer = max(crossed, key=lambda p: p.position)
        self.twist_triggered = True
        play_by_play_lines.append(
            f"\n>>> {triggerer.name} ({triggerer.piece}) passed space 13 — "
            f"a twist is drawn!"
        )
        if self.forced_twist:
            from twists import apply_named_twist
            apply_named_twist(self, triggerer, play_by_play_lines, self.forced_twist)
        else:
            from twists import draw_and_apply_twist
            draw_and_apply_twist(self, triggerer, play_by_play_lines)
        play_by_play_lines.append("")  # blank line for readability

    def _doppelgangster_steal_power(self, doppelgangster, target, play_by_play_lines):
        """Swap Doppelgangster's Python class to the target's class, preserving
        race state (position, chips, finished/eliminated/tripped flags, etc.).
        The transformed Doppelgangster keeps their "Doppelgangster" piece name
        but immediately uses the target class's POWER_PHASES and methods.

        Implementation: snapshot the base-state attrs, swap __class__, re-run
        the target class's __init__ (to set up class-specific instance state
        like NormalHarry.is_transformed or Nemesis.has_picked_nemesis), then
        restore the snapshot. The __init__ call also resets base state (name,
        piece, position, chips, etc.); the snapshot restore puts those back."""
        target_class = type(target)
        from characters.doppelgangster import Doppelgangster as _Dop
        if target_class is _Dop or target_class is Character:
            return  # no power worth stealing

        preserved = {
            'position': doppelgangster.position,
            'previous_position': doppelgangster.previous_position,
            'finished': False,
            'eliminated': False,
            'tripped': doppelgangster.tripped,
            'turn_start_position': doppelgangster.turn_start_position,
            'last_roll': doppelgangster.last_roll,
            'skip_main_move': doppelgangster.skip_main_move,
            'main_move_multiplier': doppelgangster.main_move_multiplier,
            'ability_activations': doppelgangster.ability_activations,
            'gold_chips': doppelgangster.gold_chips,
            'silver_chips': doppelgangster.silver_chips,
            'bronze_chips': doppelgangster.bronze_chips,
        }
        if hasattr(doppelgangster, 'player_number'):
            preserved['player_number'] = doppelgangster.player_number
        name = doppelgangster.name
        piece = doppelgangster.piece  # stays "Doppelgangster"

        doppelgangster.__class__ = target_class
        try:
            target_class.__init__(doppelgangster, name, piece)
        except Exception as exc:
            play_by_play_lines.append(
                f"  Doppelgangster power transfer init error ({exc!r}) — proceeding anyway."
            )

        for k, v in preserved.items():
            setattr(doppelgangster, k, v)

        play_by_play_lines.append(
            f"  Doppelgangster now wields the power of {target_class.__name__}."
        )
        # Credit Doppelgangster with the intercept itself as an ability use.
        # Post-swap, the stolen class's own register_ability_use calls will
        # also increment this same counter (since they fire on the
        # Doppelgangster instance), keeping all activity attributed to
        # "Doppelgangster" in the stats.
        doppelgangster.register_ability_use(
            self, play_by_play_lines,
            description=f"Doppelgangster (stole {target_class.__name__})"
        )

    def _active_stunners_near(self, player):
        """Return the list of active (non-suppressed) Stunners within 1 space
        of `player`. Empty list if none. Used by roll_die for the override
        and to credit each adjacent Stunner with an ability activation."""
        return [
            p for p in self.players
            if p.piece == "Stunner"
            and p is not player
            and not p.finished
            and p not in self.eliminated_players
            and abs(p.position - player.position) <= 1
            and not self.is_power_suppressed_for(p)
        ]

    def is_near_stunner(self, player):
        """True if any active (non-suppressed) Stunner is within 1 space of
        the given player. Used by Game.roll_die to force a 1 for any roll
        the player makes, per Stunner's spec: 'Other racers within 1 space
        of me roll a 1 for all rolls.'"""
        return bool(self._active_stunners_near(player))

    def roll_die(self, player, play_by_play_lines=None, low=1, high=6):
        """Roll a die for `player`. Returns 1 (regardless of `low`/`high`)
        when Stunner's proximity rule applies — per Stunner's spec, that's
        'roll a 1 for all rolls', interpreted literally even if a caller
        passes an unusual range. Otherwise returns random.randint(low, high).

        Use this instead of bare random.randint anywhere a CHARACTER ROLLS
        a die that the game treats as a roll (main move, Duelist duel,
        TheHose, Soulmate, MrDiceGuy, ShowOff). Internal randoms that
        the spec doesn't call rolls — Genius's lucky number, Cheatah's
        chosen value/guess, Mole's leader tiebreak, MagicalAthlete spell
        target picks — stay on random.randint.

        Each override is an ability use: every adjacent Stunner is credited
        via register_ability_use, which also triggers Scoocher (Scoocher's
        rule is to react to any ability use, and a roll forced to 1 is an
        ability use). This can fire many times per turn (MrDiceGuy's 6 dice,
        ShowOff's chain) — that's intentional."""
        nearby = self._active_stunners_near(player)
        if nearby:
            if play_by_play_lines is not None:
                play_by_play_lines.append(
                    f"  Stunner forces {player.name} ({player.piece}) to roll 1."
                )
            for s in nearby:
                s.register_ability_use(self, play_by_play_lines)
            return 1
        # Twists: Randomness Ceased — this player's roll is locked at their
        # snapshot value for the rest of the race. Clamped to the requested
        # range so unusual callers (e.g., a hypothetical roll_die(low=4, high=6))
        # still get a value in their expected band.
        fixed = self.twist_state.get('fixed_rolls', {}).get(id(player))
        if fixed is not None:
            return max(low, min(fixed, high))
        return random.randint(low, high)

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.turn_order)
        self._scoocher_recursion_depth = 0

    @property
    def current_player(self):
        return self.players[self.turn_order[self.current_player_index]]

    def should_game_end(self, play_by_play_lines):
        if getattr(self, 'race_cancelled', False):
            return True
        if len(self.finished_players) >= 2 or len(self.players) - len(self.finished_players) - len(self.eliminated_players) <= 1:
            return True
        for p in self.players:
            if p.piece == "Mastermind":
                return p.check_prediction(self, play_by_play_lines)
        return False
                
    def finish_player(self, player, play_by_play_lines):
        if not player.finished:
            # Doppelgangster intercept: when the FIRST racer crosses the finish
            # line, if there's an active *untransformed* Doppelgangster (not
            # the finisher), the finisher is eliminated and Doppelgangster
            # steals their class. We use `isinstance(p, Doppelgangster)`
            # rather than the piece-name check so a Doppelgangster whose
            # class has already been swapped (one-shot ability) doesn't
            # re-intercept. Skipped during Season Finale.
            from characters.doppelgangster import Doppelgangster as _Dop
            if (len(self.finished_players) == 0
                    and not isinstance(player, _Dop)
                    and not self.twist_state.get('season_finale_active')):
                dop = next(
                    (p for p in self.players
                     if isinstance(p, _Dop)
                     and not p.finished
                     and p not in self.eliminated_players),
                    None,
                )
                if dop is not None:
                    play_by_play_lines.append(
                        f"!! Doppelgangster intercepts! {player.name} ({player.piece}) "
                        f"would have finished 1st — eliminated instead, power stolen."
                    )
                    self.eliminate_player(player, play_by_play_lines)
                    self._doppelgangster_steal_power(dop, player, play_by_play_lines)
                    return

            player.finished = True
            self.finished_players.append(player)

            # Twists: Season Finale — "racing for all the points." The first
            # of the two finalists to finish takes BOTH gold and silver; the
            # other finalist gets nothing. Both finishers go through this
            # branch (no fall-through to the normal placement-chip logic) so
            # the loser doesn't pick up an accidental silver.
            if self.twist_state.get('season_finale_active'):
                if len(self.finished_players) == 1:
                    player.gold_chips += 1
                    player.silver_chips += 1
                    play_by_play_lines.append(
                        f"{player.name} ({player.piece}) wins the Season Finale 1v1 — "
                        f"takes the gold AND silver chips!"
                    )
                else:
                    play_by_play_lines.append(
                        f"{player.name} ({player.piece}) finished after losing the "
                        f"Season Finale — no placement chips."
                    )
                return

            # Award gold or silver chips based on finish position
            if len(self.finished_players) == 1:
                # First place gets a gold chip (5 points)
                player.gold_chips += 1
                play_by_play_lines.append(f"{player.name} ({player.piece}) finished the race in 1st place and received a gold chip!")
            elif len(self.finished_players) == 2:
                # Second place gets a silver chip (3 points)
                player.silver_chips += 1
                play_by_play_lines.append(f"{player.name} ({player.piece}) finished the race in 2nd place and received a silver chip!")
            else:
                play_by_play_lines.append(f"{player.name} ({player.piece}) finished the race!")

    def eliminate_player(self, player, play_by_play_lines):
        if player not in self.eliminated_players:
            self.eliminated_players.append(player)
            play_by_play_lines.append(f"{player.name} ({player.piece}) was eliminated!")

    def assign_final_placements(self):
        placements = []
        for i, player in enumerate(self.finished_players):
            placements.append((f"{i+1}st", player))
        remaining_players = sorted([p for p in self.players if not p.finished and p not in self.eliminated_players], key=lambda x: (-x.position, x.player_number))
        for i, player in enumerate(remaining_players):
            placements.append((f"{len(self.finished_players) + i + 1}st", player))
        for i, player in enumerate(reversed(self.eliminated_players)):
            placements.append((f"{len(self.players) - i}st", player))
        return placements

    def trigger_scoocher(self, play_by_play_lines):
        # Check if we're already too deep in recursive calls
        max_depth = 3
        if self._recursion_depths['scoocher'] >= max_depth:
            play_by_play_lines.append("WARNING: Skipping Scoocher movement to prevent infinite loop")
            return
        
        # Increment recursion counter
        self._recursion_depths['scoocher'] += 1
        
        try:
            for player in self.players:
                if player.piece == "Scoocher" and not player.finished:
                    # Make sure we're not in an infinite movement loop
                    if self._recursion_depths['movement'] <= 2:
                        player.move(self, play_by_play_lines, 1)
                        player.ability_activations += 1
                        play_by_play_lines.append(f"{player.name} ({player.piece}) used ability: Scoocher")
                        play_by_play_lines.append(f"{player.name} (Scoocher) moved 1 space because another player used their ability.")
                    else:
                        play_by_play_lines.append(f"WARNING: Movement limit reached for {player.name} (Scoocher). Skipping to prevent recursion.")
        finally:
            # Decrement recursion counter
            self._recursion_depths['scoocher'] -= 1

    def change_turn_order(self, skipper, play_by_play_lines):
        skipper_index = self.players.index(skipper)
        if (self.current_player_index + 1) % len(self.turn_order) != skipper_index:
            self.turn_order.remove(skipper_index)
            insert_pos = (self.current_player_index + 1) % len(self.turn_order)
            self.turn_order.insert(insert_pos, skipper_index)
            play_by_play_lines.append(f"Player {skipper.player_number} (Skipper) has changed the turn order to go next!")
            self.current_player_index = (insert_pos - 1) % len(self.turn_order)

    def resolve_phase(self, phase, current_player, play_by_play_lines, context=None):
        """Resolve all powers in a specific phase following official rules order.

        Resolution order within each phase (per official rules):
        1. Racetrack spaces (board effects)
        2. Current player
        3. Other players in turn order (clockwise)

        Args:
            phase: PowerPhase enum value
            current_player: The player whose turn it is
            play_by_play_lines: List to append play-by-play messages
            context: Dict with phase-specific data (e.g., {'roll': 5, 'spaces': 3})

        Returns:
            Modified context dict (e.g., with updated 'roll' value)
        """
        context = context or {}

        # STEP 1: Board effects (Racetrack spaces) - only for POST_MOVEMENT phase
        # Note: Most board effects happen via on_enter() in move() method during MOVEMENT phase
        # This is here for any board effects that need to use the phase system
        if phase == PowerPhase.POST_MOVEMENT:
            if not current_player.finished and 0 <= current_player.position < self.board.length:
                current_space = self.board.spaces[current_player.position]
                # Note: on_enter() was already called during move(), so we don't call it again here
                # This step is reserved for future board effects that might use the phase system
                pass

        # STEP 2: Current player's power
        # Always execute MOVEMENT phase (core mechanic), otherwise check POWER_PHASES
        if phase == PowerPhase.MOVEMENT or phase in current_player.POWER_PHASES:
            result = self._execute_phase_action(current_player, phase, current_player,
                                               play_by_play_lines, context)
            if result is not None:
                # Update context with returned value (typically a modified roll)
                if isinstance(result, int):
                    context['roll'] = result
                elif isinstance(result, dict):
                    context.update(result)

        # STEP 3: Other players in turn order (clockwise)
        for player_index in self.turn_order:
            other_player = self.players[player_index]
            # Other players participate if they have this phase declared
            # (e.g., Gunk modifying rolls, Inchworm reacting to die rolls)
            if other_player != current_player and phase in other_player.POWER_PHASES:
                result = self._execute_phase_action(other_player, phase, current_player,
                                                    play_by_play_lines, context)
                if result is not None:
                    if isinstance(result, int):
                        context['roll'] = result
                    elif isinstance(result, dict):
                        context.update(result)

        return context

    def _execute_phase_action(self, power_owner, phase, current_player,
                             play_by_play_lines, context):
        """Execute the appropriate method for a character in this phase.

        Args:
            power_owner: The character whose power is executing
            phase: The current PowerPhase
            current_player: The player whose turn it is
            play_by_play_lines: List for messages
            context: Dict with phase data

        Returns:
            Result of the action (typically None or a modified roll value)
        """
        # Null: racers ahead of Null have no powers.
        # MOVEMENT is special — it's the core mechanic, not a "power" per se,
        # so we always allow it. Other phases skip when suppressed.
        if phase != PowerPhase.MOVEMENT and self.is_power_suppressed_for(power_owner):
            return None
        try:
            if phase == PowerPhase.PRE_ROLL:
                # Only current player executes pre-roll actions
                if power_owner == current_player:
                    return power_owner.pre_move_action(self, play_by_play_lines)

            elif phase == PowerPhase.DIE_ROLL_TRIGGER:
                # All players can react to a roll
                return power_owner.trigger_on_main_move_roll(
                    current_player, self, context.get('roll', 0), play_by_play_lines)

            elif phase == PowerPhase.ROLL_MODIFICATION:
                # All players can modify the current player's roll
                if hasattr(power_owner, 'modify_other_roll'):
                    return power_owner.modify_other_roll(
                        current_player, self, play_by_play_lines, context.get('roll', 0))

            elif phase == PowerPhase.MOVEMENT:
                # Only current player moves (unless following via Suckerfish, etc.)
                if power_owner == current_player:
                    power_owner.move(self, play_by_play_lines, context.get('spaces', 0))

            elif phase == PowerPhase.POST_MOVEMENT:
                # This is handled separately for board effects in resolve_phase()
                # Character-specific post-movement (like HugeBaby) happens here
                # This triggers via on_another_player_move() from within move()
                pass

            elif phase == PowerPhase.OTHER_REACTIONS:
                # This phase is for reactions that happen after movement completes
                # Most are handled via on_another_player_move() called from within move()
                # But some like Romantic need explicit handling
                pass

            elif phase == PowerPhase.POST_TURN:
                # End-of-turn actions for all players
                return power_owner.post_turn_actions(self, current_player, play_by_play_lines)

        except TurnEventCapExceeded:
            # Watchdog exception — must propagate up to _take_turn_or_stun's
            # catch so the diagnostic gets logged and the turn aborts cleanly.
            raise
        except Exception as e:
            play_by_play_lines.append(
                f"ERROR: {power_owner.name} ({power_owner.piece}) failed in {phase}: {str(e)}"
            )
            import traceback
            traceback.print_exc()

        return None
            
    def get_ability_statistics(self):
        """Returns a dictionary with ability activation counts for each character."""
        return {player.piece: getattr(player, 'ability_activations', 0) for player in self.players}
        
    def get_chip_statistics(self):
        """Returns chip DELTAs (current - starting) for each character. The
        avg-points metric should reflect points earned during the race, not
        chips seeded before it (random_starting_bronze, speeddemon_starting_points).
        Negative values are possible (e.g., Hotel charges, Spoilsport revokes)."""
        chip_stats = {}
        baseline = getattr(self, '_chip_baseline', {})
        for player in self.players:
            start_gold, start_silver, start_bronze = baseline.get(
                id(player), (0, 0, 0)
            )
            gold_delta = player.gold_chips - start_gold
            silver_delta = player.silver_chips - start_silver
            bronze_delta = player.bronze_chips - start_bronze
            chip_stats[player.piece] = {
                'gold': gold_delta,
                'silver': silver_delta,
                'bronze': bronze_delta,
                'points': gold_delta * 5 + silver_delta * 3 + bronze_delta,
            }
        return chip_stats

class _CappedLogList(list):
    """List subclass that caps append/extend after `cap` items.
    After the cap is hit, a single truncation marker is added and further
    appends become no-ops. Used inside run_simulations to keep per-race log
    memory bounded when reactive characters create cascade fan-out."""

    def __init__(self, cap=5000):
        super().__init__()
        self._cap = cap
        self._truncated = False

    def append(self, item):
        if len(self) < self._cap:
            list.append(self, item)
        elif not self._truncated:
            list.append(self, f"[Per-race log truncated at {self._cap} lines]")
            self._truncated = True

    def extend(self, items):
        for item in items:
            self.append(item)


def _run_single_simulation(character_names, board_type=DEFAULT_BOARD_TYPE, random_turn_order=False):
    play_by_play_lines = []
    game = Game(character_names, board_type=board_type, random_turn_order=random_turn_order)
    turns, final_placements = game.run(play_by_play_lines)
    # Add board info to play-by-play
    play_by_play_lines.insert(0, f"Board: {game.board.get_display_name()}")
    return turns, final_placements, play_by_play_lines, game.board.board_type

def run_simulations(num_simulations, num_players, board_type=DEFAULT_BOARD_TYPE, fixed_characters=None, random_turn_order=False, collect_detailed_logs=False, allowed_characters=None, speeddemon_threshold=4, speeddemon_starting_points=3, speeddemon_check_timing="start", showoff_threshold=5, random_starting_bronze=True, null_main_move_penalty=1, spoilsport_threshold=5, nemesis_warp_range=5, random_board_pool=None, cheatah_alt_mode=True, forced_twist=None):
    """Run multiple simulations and return statistics with proper ability tracking.

    Args:
        collect_detailed_logs: If True, collects detailed play-by-play logs (memory intensive).
                               Set to False for production/Streamlit to save memory.
    """
    # Redirect print output to capture debug statements
    import io
    import sys
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        all_turns = []
        turns_by_board = {"Mild": [], "Wild": [], "Sportals": [], "Twists": []}
        finish_positions = {char: [] for char in character_abilities.keys()}
        ability_activations = {char: [] for char in character_abilities.keys()}
        appearance_count = {char: 0 for char in character_abilities.keys()}  # Track appearances
        chip_statistics = {char: [] for char in character_abilities.keys()}  # Track chip statistics
        win_counts = {char: 0 for char in character_abilities.keys()}  # Track 1st-place finishes

        # Only collect detailed logs if requested (saves memory for Streamlit)
        all_play_by_play = [] if collect_detailed_logs else None
        complete_logs = [] if collect_detailed_logs else None

        # Track board type usage
        board_type_counts = {"Mild": 0, "Wild": 0, "Sportals": 0, "Twists": 0}
        
        sampling_pool = allowed_characters if allowed_characters else list(character_abilities.keys())

        for i in range(num_simulations):
            selected_characters = fixed_characters if fixed_characters else random.sample(sampling_pool, num_players)
            
            # Run the simulation with the specified board type.
            # Per-race log lines are capped to keep memory bounded with V1+V2
            # reactive cascades (Mole+Romantic fan-out + bonus turns).
            game = Game(selected_characters, board_type=board_type, random_turn_order=random_turn_order, speeddemon_threshold=speeddemon_threshold, speeddemon_starting_points=speeddemon_starting_points, speeddemon_check_timing=speeddemon_check_timing, showoff_threshold=showoff_threshold, random_starting_bronze=random_starting_bronze, null_main_move_penalty=null_main_move_penalty, spoilsport_threshold=spoilsport_threshold, nemesis_warp_range=nemesis_warp_range, random_board_pool=random_board_pool, cheatah_alt_mode=cheatah_alt_mode, forced_twist=forced_twist)
            play_by_play_lines = _CappedLogList(cap=5000) if collect_detailed_logs else _CappedLogList(cap=500)
            turns, final_placements = game.run(play_by_play_lines)
            
            # Add board info to play-by-play
            play_by_play_lines.insert(0, f"Board: {game.board.get_display_name()}")
            used_board_type = game.board.board_type
            
            # Track which board type was used
            if used_board_type in board_type_counts:
                board_type_counts[used_board_type] += 1
            if used_board_type in turns_by_board:
                turns_by_board[used_board_type].append(turns)
                
            # Count appearances for each character in this race
            for char in selected_characters:
                appearance_count[char] += 1
            
            # Store the complete logs (only if collecting detailed logs)
            if collect_detailed_logs:
                complete_logs.append("\n".join(play_by_play_lines))

            # Debug output - include ability activation counts (only if collecting detailed logs)
            if collect_detailed_logs:
                debug_info = [f"--- Simulation {i+1} ---"]
                debug_info.append(f"Selected characters: {selected_characters}")
                debug_info.append("Ability activations:")
            
            try:
                # Get the game object from the most recent simulation
                current_game = game  # This was the issue - 'game' variable wasn't defined in this scope

                # Get ability statistics
                char_ability_stats = current_game.get_ability_statistics()

                # Debug output (only if collecting detailed logs)
                if collect_detailed_logs:
                    debug_info.append("Ability activations:")
                    for char, count in char_ability_stats.items():
                        debug_info.append(f"  {char}: {count}")

                # Store for averaging
                for char, count in char_ability_stats.items():
                    if char in ability_activations:
                        ability_activations[char].append(count)

                # Get chip statistics
                chip_stats = current_game.get_chip_statistics()

                # Debug output (only if collecting detailed logs)
                if collect_detailed_logs:
                    debug_info.append("Chip statistics:")
                    for char, stats in chip_stats.items():
                        debug_info.append(f"  {char}: {stats['points']} points (G:{stats['gold']}, S:{stats['silver']}, B:{stats['bronze']})")

                # Track chip statistics (we'll add it to the return values)
                for char, stats in chip_stats.items():
                    if char not in chip_statistics:
                        chip_statistics[char] = []
                    chip_statistics[char].append(stats)
            except Exception as e:
                if collect_detailed_logs:
                    debug_info.append(f"Error getting statistics: {str(e)}")

            # Add debug info to play-by-play (only if collecting detailed logs)
            if collect_detailed_logs:
                all_play_by_play.extend(debug_info)
                all_play_by_play.extend(play_by_play_lines)
            
            all_turns.append(turns)
            
            for place, player in final_placements:
                pos = int(place[:-2])
                finish_positions[player.piece].append(pos)
                if pos == 1:
                    win_counts[player.piece] += 1
        
        average_turns = sum(all_turns) / num_simulations if all_turns else 0
        average_finish_positions = {char: (sum(positions) / len(positions)) if positions else None for char, positions in finish_positions.items()}
        
        # Calculate average ability activations with debug output
        average_ability_activations = {}
        for char, counts in ability_activations.items():
            if counts:
                avg = sum(counts) / len(counts)
                average_ability_activations[char] = avg
                if collect_detailed_logs:
                    all_play_by_play.append(f"Average ability uses for {char}: {avg:.2f}")
            else:
                average_ability_activations[char] = 0
                if collect_detailed_logs:
                    all_play_by_play.append(f"No data for {char} ability uses")
        
        # Calculate average chip statistics
        average_chip_stats = {}
        for char, stats_list in chip_statistics.items():
            if stats_list:
                # Calculate averages for each chip type and points
                total_gold = sum(s['gold'] for s in stats_list)
                total_silver = sum(s['silver'] for s in stats_list)
                total_bronze = sum(s['bronze'] for s in stats_list)
                total_points = sum(s['points'] for s in stats_list)
                num_appearances = len(stats_list)
                
                average_chip_stats[char] = {
                    'gold_avg': total_gold / num_appearances,
                    'silver_avg': total_silver / num_appearances,
                    'bronze_avg': total_bronze / num_appearances,
                    'points_avg': total_points / num_appearances
                }

                if collect_detailed_logs:
                    all_play_by_play.append(f"Average points for {char}: {total_points / num_appearances:.2f}")
            else:
                average_chip_stats[char] = {
                    'gold_avg': 0, 'silver_avg': 0, 'bronze_avg': 0, 'points_avg': 0
                }

        # Add character appearance counts to the debug output (only if collecting detailed logs)
        if collect_detailed_logs:
            all_play_by_play.append("\nCharacter appearance counts:")
            for char, count in appearance_count.items():
                if count > 0:
                    all_play_by_play.append(f"{char}: {count} races")

            # Add board type usage statistics
            all_play_by_play.append("\nBoard type usage:")
            for board_type, count in board_type_counts.items():
                if count > 0:
                    percentage = (count / num_simulations) * 100
                    all_play_by_play.append(f"{board_type} Board: {count} races ({percentage:.1f}%)")
        
        # Return empty list for play-by-play if detailed logs weren't collected
        play_by_play_result = all_play_by_play if collect_detailed_logs else []
        average_turns_by_board = {
            bt: (sum(t) / len(t)) if t else None for bt, t in turns_by_board.items()
        }
        return average_turns, average_finish_positions, play_by_play_result, average_ability_activations, appearance_count, average_chip_stats, board_type_counts, win_counts, average_turns_by_board
    finally:
        # Restore stdout
        sys.stdout = original_stdout

def write_summary_to_file(filename, num_simulations, num_players, selected_characters, average_turns, average_finish_positions):
    with open(filename, 'w') as file:
        file.write(f"Number of simulations: {num_simulations}\nNumber of players: {num_players}\n")
        if selected_characters:
            file.write(f"Characters used: {', '.join(selected_characters)}\n")
        file.write(f"Average number of turns per game: {average_turns:.2f}\n\nAverage finish position of each character (best to worst):\n")
        sorted_positions = sorted(average_finish_positions.items(), key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf')))
        for char, avg_position in sorted_positions:
            file.write(f"{char}: {avg_position:.2f}\n" if avg_position is not None else f"{char}: Did not participate in any simulation\n")

def write_play_by_play_to_file(filename, play_by_play_lines):
    with open(filename, 'w') as file:
        for line in play_by_play_lines:
            file.write(line + '\n')