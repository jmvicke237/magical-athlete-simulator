# game_simulation.py
import random
from config import character_abilities, BOARD_LENGTH, MAX_TURNS, CORNER_POSITION, BOARD_TYPES, DEFAULT_BOARD_TYPE
from characters.base_character import Character
from board import Board
from power_system import PowerPhase
from debug_utils import TurnEventCapExceeded

class Game:
    def __init__(self, character_names, board_type=DEFAULT_BOARD_TYPE, board=None, random_turn_order=False, prometheus_threshold=3, prometheus_starting_points=0, prometheus_check_timing="end", highroller_threshold=8, random_starting_bronze=False):
        self.players = []
        self.prometheus_threshold = prometheus_threshold  # Lead size that triggers Prometheus self-elimination (strict > comparison)
        self.prometheus_check_timing = prometheus_check_timing  # "start" or "end" — when the elimination check fires
        self._prometheus_starting_points = prometheus_starting_points  # Granted as bronze chips after player creation
        self.highroller_threshold = highroller_threshold  # HighRoller stops rolling once total >= this
        self._random_starting_bronze = random_starting_bronze  # Each racer gets random 0-5 starting bronze chips
        
        # Handle board creation
        if board:
            self.board = board
        else:
            # If board_type is Random, choose between Mild and Wild
            actual_board_type = board_type
            if board_type == "Random":
                actual_board_type = random.choice(["Mild", "Wild"])
            
            self.board = Board(board_type=actual_board_type, corner_position=CORNER_POSITION)
        
        self.finished_players = []
        self.eliminated_players = []
        self.turn_order = []
        self.current_player_index = 0
        self.race_cancelled = False  # Set by Spoilsport (or similar) to end the race
        self._last_main_roll = None  # Most recent main-roll value across all players (used by Apprentice)
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
        
        self._create_players(character_names, random_turn_order)

        # Random starting bronze chips per racer (0-5 each), applied first.
        if self._random_starting_bronze:
            for player in self.players:
                player.bronze_chips += random.randint(0, 5)

        # Grant Prometheus starting bronze chips (overrides random for Prometheus).
        if self._prometheus_starting_points > 0:
            for player in self.players:
                if player.piece == "Prometheus":
                    player.bronze_chips = self._prometheus_starting_points

        # Snapshot starting chips AFTER all seeding so get_chip_statistics can
        # return deltas (points earned/lost during the race, not counting
        # chips granted before the race started).
        self._chip_baseline = {
            id(p): (p.gold_chips, p.silver_chips, p.bronze_chips)
            for p in self.players
        }

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

                if self.should_game_end(play_by_play_lines):
                    break
                self.next_player()

        # End-of-race hooks (e.g., Sandbag's no-corner bonus). Antimag
        # suppression applies — racers ahead of Antimag don't get end-of-race powers.
        for player in self.players:
            if not self.is_power_suppressed_for(player):
                player.on_race_end(self, play_by_play_lines)

        play_by_play_lines.append("The race has ended!")

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
        """True if any active AntimagicalAthlete is in the game and the given
        character is strictly ahead of them. AntimagicalAthlete's spec:
        "Racers ahead of me have no powers." Position is checked dynamically
        at each call site so suppression updates immediately as racers move."""
        for p in self.players:
            if (p.piece == "AntimagicalAthlete"
                    and p is not character
                    and not p.finished
                    and p not in self.eliminated_players
                    and character.position > p.position):
                return True
        return False

    def _take_turn_or_stun(self, player, play_by_play_lines):
        """Take the player's turn, unless an active Stunner is within 1 space.
        Stun completely skips the turn (NOT a trip — no abilities fire, no
        Trip status is consumed). Wraps the turn in a watchdog: if more than
        Game._turn_event_cap move/jump/ability events fire during this turn,
        TurnEventCapExceeded is raised, the turn aborts, and a diagnostic
        line is captured (so we can identify the bad character combo)."""
        # Reset event counter BEFORE any logic in this function (including the
        # stunner branch which calls register_ability_use). Otherwise a high
        # leftover count from the previous aborted turn would re-trip the
        # watchdog before we get to the try-block.
        self._turn_event_count = 0

        # Wrap EVERYTHING in the try so any TurnEventCapExceeded is caught,
        # including the stunner branch's register_ability_use.
        try:
            stunner = self._find_active_stunner_near(player)
            if stunner is not None:
                play_by_play_lines.append(
                    f"{player.name} ({player.piece}) is stunned by "
                    f"{stunner.name} ({stunner.piece}) and skips their turn."
                )
                stunner.register_ability_use(self, play_by_play_lines, description="Stunner")
                return

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

    def _find_active_stunner_near(self, player):
        for p in self.players:
            if (p.piece == "Stunner"
                    and p is not player
                    and not p.finished
                    and p not in self.eliminated_players
                    and abs(p.position - player.position) <= 1):
                return p
        return None

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
            player.finished = True
            self.finished_players.append(player)
            
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
        # AntimagicalAthlete: racers ahead of Antimag have no powers.
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
        chips seeded before it (random_starting_bronze, prometheus_starting_points).
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

def run_simulations(num_simulations, num_players, board_type=DEFAULT_BOARD_TYPE, fixed_characters=None, random_turn_order=False, collect_detailed_logs=False, allowed_characters=None, prometheus_threshold=3, prometheus_starting_points=0, prometheus_check_timing="end", highroller_threshold=8, random_starting_bronze=False):
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
        turns_by_board = {"Mild": [], "Wild": []}
        finish_positions = {char: [] for char in character_abilities.keys()}
        ability_activations = {char: [] for char in character_abilities.keys()}
        appearance_count = {char: 0 for char in character_abilities.keys()}  # Track appearances
        chip_statistics = {char: [] for char in character_abilities.keys()}  # Track chip statistics
        win_counts = {char: 0 for char in character_abilities.keys()}  # Track 1st-place finishes

        # Only collect detailed logs if requested (saves memory for Streamlit)
        all_play_by_play = [] if collect_detailed_logs else None
        complete_logs = [] if collect_detailed_logs else None

        # Track board type usage
        board_type_counts = {"Mild": 0, "Wild": 0}
        
        sampling_pool = allowed_characters if allowed_characters else list(character_abilities.keys())

        for i in range(num_simulations):
            selected_characters = fixed_characters if fixed_characters else random.sample(sampling_pool, num_players)
            
            # Run the simulation with the specified board type.
            # Per-race log lines are capped to keep memory bounded with V1+V2
            # reactive cascades (Mole+Romantic fan-out + bonus turns).
            game = Game(selected_characters, board_type=board_type, random_turn_order=random_turn_order, prometheus_threshold=prometheus_threshold, prometheus_starting_points=prometheus_starting_points, prometheus_check_timing=prometheus_check_timing, highroller_threshold=highroller_threshold, random_starting_bronze=random_starting_bronze)
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