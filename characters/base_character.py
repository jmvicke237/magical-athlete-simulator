# characters/base_character.py
import random
from power_system import PowerPhase

class Character:
    """Base character class for Magical Athlete racers.

    Power Phase System:
    Characters can declare which phases they participate in by setting the
    POWER_PHASES class attribute to a set of PowerPhase values.

    Example:
        class Gunk(Character):
            POWER_PHASES = {PowerPhase.ROLL_MODIFICATION}

    If POWER_PHASES is not defined, the character has no special abilities
    and only uses standard movement.
    """

    # Characters with abilities should override this
    POWER_PHASES = set()
    def __init__(self, name, piece):
        self.name = name
        self.piece = piece
        self.position = 0
        self.previous_position = 0
        self.finished = False
        self.eliminated = False
        self.tripped = False
        self.turn_start_position = 0
        self.last_roll = -1
        self.skip_main_move = False
        self.ability_activations = 0
        
        # Chip tracking
        self.gold_chips = 0
        self.silver_chips = 0
        self.bronze_chips = 0

    def take_turn(self, game, play_by_play_lines):
        """Execute a full turn using the phase-based power resolution system.

        Phase order (per official rules):
        1. PRE_ROLL - Before rolling (Cheerleader, Hypnotist, Party Animal)
        2. DIE_ROLL_TRIGGER - Triggered by roll (Inchworm, Skipper)
        3. ROLL_MODIFICATION - Modify roll (Gunk, Coach, Blimp)
        4. MOVEMENT - Execute movement
        5. POST_MOVEMENT - Board effects, character reactions (HugeBaby)
        6. OTHER_REACTIONS - Other players react (Romantic, Scoocher)
        7. POST_TURN - End of turn (Duelist)
        """
        self.turn_start_position = self.position
        self.last_roll = -1

        # Check if tripped
        if self.tripped:
            self.tripped = False
            self.skip_main_move = True
            play_by_play_lines.append(f"{self.name} ({self.piece}) is tripped and skips their main move.")

        # PHASE 1: PRE_ROLL - Abilities before rolling
        game.resolve_phase(PowerPhase.PRE_ROLL, self, play_by_play_lines)

        if not self.skip_main_move:
            # Roll the die
            roll = self.main_roll(game, play_by_play_lines)
            self.last_roll = roll

            # Handle rerolls (Magician, Dicemonger)
            # Note: Rerolls happen before triggers, so we handle them specially
            for player_index in game.turn_order:
                other_player = game.players[player_index]
                if hasattr(other_player, "reroll_main_roll"):
                    roll = other_player.reroll_main_roll(self, game, play_by_play_lines, roll)
                    self.last_roll = roll

            # PHASE 2: DIE_ROLL_TRIGGER - Powers triggered by the roll value (before mods)
            context = game.resolve_phase(PowerPhase.DIE_ROLL_TRIGGER, self, play_by_play_lines,
                                        context={'roll': roll})

            # Check if Inchworm or similar set skip_main_move
            if not self.skip_main_move:
                # PHASE 3: ROLL_MODIFICATION - Modify the roll value
                context = game.resolve_phase(PowerPhase.ROLL_MODIFICATION, self, play_by_play_lines,
                                            context={'roll': roll})
                roll = context.get('roll', roll)
                self.last_roll = roll

                # PHASE 4: MOVEMENT - Execute the move
                game.resolve_phase(PowerPhase.MOVEMENT, self, play_by_play_lines,
                                  context={'spaces': roll})

                # PHASE 5: POST_MOVEMENT - Board effects and character reactions
                # Note: This is mostly handled within move() via on_enter() and on_another_player_move()
                # But we call it here for completeness and to ensure proper ordering
                game.resolve_phase(PowerPhase.POST_MOVEMENT, self, play_by_play_lines)

        # Execute post-move ability (for backwards compatibility with characters that use this)
        self.post_move_ability(game, play_by_play_lines)

        # PHASE 6: OTHER_REACTIONS - Additional reactions
        # Note: Most reactions happen via on_another_player_move() called from within move()
        game.resolve_phase(PowerPhase.OTHER_REACTIONS, self, play_by_play_lines)

        # PHASE 7: POST_TURN - End of turn actions
        game.resolve_phase(PowerPhase.POST_TURN, self, play_by_play_lines)

        # Reset skip_main_move flag at end of turn
        if self.skip_main_move:
            self.skip_main_move = False

        # Clear state history at end of turn to prepare for next turn
        game.clear_state_history()

    def pre_move_action(self, game, play_by_play_lines):
        pass

    def main_roll(self, game, play_by_play_lines):
        roll = random.randint(1, 6)
        play_by_play_lines.append(f"{self.name} ({self.piece}) rolled a {roll}")
        self.last_roll = roll
        return roll
    
    def modify_roll(self, game, play_by_play_lines, roll):
        """Iterate through all *other* players in turn order and apply their modifications."""
        for player_index in game.turn_order:
            other_player = game.players[player_index]
            if hasattr(other_player, "modify_other_roll"):
                roll = other_player.modify_other_roll(self, game, play_by_play_lines, roll)
        return roll
    
    def move(self, game, play_by_play_lines, spaces): # If this is changed, also change Leaptoad
        """Move a character, with state-based loop detection."""
        # Rule: "Move 0" does not count as moving and should not trigger abilities
        if spaces == 0:
            return

        # Check for infinite loop (repeating game state)
        # This also adds current state to history for tracking across ability chains
        if game.check_for_state_loop(f"{self.name} ({self.piece})", play_by_play_lines):
            return

        # Import the logger for recursion tracking
        from debug_utils import log_recursion_state, logger

        # Log state only when approaching recursion limits (kept for debugging)
        log_recursion_state(game, "move", self)

        # Safety fallback: Guard against excessive recursion depth
        if game._recursion_depths['movement'] >= game._max_recursion_depth:
            play_by_play_lines.append(f"WARNING: Maximum movement recursion depth ({game._max_recursion_depth}) reached for {self.name} ({self.piece})! Stopping recursion.")

            # Log critical info about the recursion only when it happens
            position_info = f"position={self.position}, spaces={spaces}"
            logger.error(f"Movement recursion limit reached for {self.name} ({self.piece}) at {position_info}")
            return

        # Increment recursion counter
        game._recursion_depths['movement'] += 1

        try:
            if self.finished:
                return

            # Check for Stickler's rule: can't overshoot the finish line
            from characters.stickler import Stickler
            if Stickler.is_in_game(game) and self.piece != "Stickler":
                if Stickler.would_overshoot(self.position, spaces, game.board.length):
                    # Find Stickler and register ability use
                    stickler = next((p for p in game.players if p.piece == "Stickler"), None)
                    if stickler:
                        stickler.register_ability_use(game, play_by_play_lines,
                                                     f"Prevented {self.name} from overshooting")

                    play_by_play_lines.append(
                        f"{self.name} ({self.piece}) would overshoot the finish line with {spaces} spaces. No movement due to Stickler!"
                    )
                    return

            self.previous_position = self.position
            # Clamp position between 0 (Start) and game.board.length (Finish)
            self.position = max(0, min(self.position + spaces, game.board.length))

            if self.position >= game.board.length:
                self.position = game.board.length
                game.finish_player(self, play_by_play_lines)
                play_by_play_lines.append(f"{self.name} ({self.piece}) moved from {self.previous_position} to {self.position} and finished!")
            else:
                play_by_play_lines.append(f"{self.name} ({self.piece}) moved from {self.previous_position} to {self.position}")

                # Trigger board space effects
                current_space = game.board.spaces[self.position]
                current_space.on_enter(self, game, play_by_play_lines)

            # Detect and notify passed racers
            passed_racers = self.detect_passes(game, self.previous_position, self.position)
            for passed_racer in passed_racers:
                passed_racer.on_being_passed(self, game, play_by_play_lines)

            # Move Suckerfish before checking for on another_player_move to avoid conflicts
            for p in game.players:
                if p.piece == "Suckerfish" and p != self:
                    p.move_with_another(self, spaces, game, play_by_play_lines)

            # Notify other players about the movement
            for other_player in game.players:
                if other_player != self:
                    other_player.on_another_player_move(self, game, play_by_play_lines)
        finally:
            # Decrement recursion counter
            game._recursion_depths['movement'] -= 1

    def post_move_ability(self, game, play_by_play_lines):
        pass

    def on_another_player_move(self, moved_player, game, play_by_play_lines):
        pass

    def on_another_player_jump(self, jumped_player, game, play_by_play_lines):
        pass

    def on_being_passed(self, passing_player, game, play_by_play_lines):
        """Called when this character is passed by another character.

        Rule: Passing occurs when a racer starts a Move behind this racer
        and ends the same Move ahead of them.
        """
        pass

    def detect_passes(self, game, start_position, end_position):
        """Detect which racers were passed during a move from start to end position.

        Rule: "Passing: When a racer starts a Move behind a racer and ends
        the same Move ahead of them."

        Returns: List of Character objects that were passed
        """
        passed_racers = []

        for other in game.players:
            if other != self and not other.finished:
                # Check if we started behind and ended ahead
                started_behind = start_position < other.position
                ended_ahead = end_position > other.position

                if started_behind and ended_ahead:
                    passed_racers.append(other)

        return passed_racers

    def trip(self, game, play_by_play_lines):
        self.tripped = True

    def jump(self, game, position, play_by_play_lines):
        """Jump/warp a character to a position, with state-based loop detection."""
        # Check for infinite loop (repeating game state)
        # This also adds current state to history for tracking across ability chains
        if game.check_for_state_loop(f"{self.name} ({self.piece})", play_by_play_lines):
            return

        # Import the logger for recursion tracking
        from debug_utils import log_recursion_state, logger

        # Log state only when approaching recursion limits (kept for debugging)
        log_recursion_state(game, "jump", self)

        # Safety fallback: Guard against excessive recursion
        if game._recursion_depths['movement'] >= game._max_recursion_depth:
            play_by_play_lines.append(f"WARNING: Maximum jump recursion depth ({game._max_recursion_depth}) reached for {self.name} ({self.piece})! Stopping recursion.")

            # Log critical info about the recursion only when it happens
            position_info = f"from={self.position}, to={position}"
            logger.error(f"Jump recursion limit reached for {self.name} ({self.piece}) at {position_info}")
            return

        # Increment recursion counter
        game._recursion_depths['movement'] += 1

        try:
            self.previous_position = self.position
            self.position = position

            if self.position >= game.board.length:
                self.position = game.board.length
                game.finish_player(self, play_by_play_lines)
                play_by_play_lines.append(f"{self.name} ({self.piece}) jumped from {self.previous_position} to {self.position} and finished!")
            else:
                play_by_play_lines.append(f"{self.name} ({self.piece}) jumped from {self.previous_position} to {self.position}")

                # Trigger board space effects
                current_space = game.board.spaces[self.position]
                current_space.on_enter(self, game, play_by_play_lines)

            # Notify other players about the jump
            for other_player in game.players:
                if other_player != self:
                    other_player.on_another_player_jump(self, game, play_by_play_lines)
        finally:
            # Decrement recursion counter
            game._recursion_depths['movement'] -= 1

    def swap_positions(self, other_player, game, play_by_play_lines):
        """Swap positions with another player.

        Rule: Swapping does NOT count as Moving, but does trigger warp/jump effects.
        Both players exchange positions simultaneously.
        """
        if other_player.finished or self.finished:
            play_by_play_lines.append(f"Cannot swap with finished player.")
            return

        # Store positions before swap
        temp_position = self.position
        other_position = other_player.position

        # Log the swap
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) and {other_player.name} ({other_player.piece}) "
            f"swapped positions (space {temp_position} <-> space {other_position})"
        )

        # Perform the swap by jumping both players
        # Note: We jump to temp positions to avoid triggering mid-swap effects
        self.jump(game, other_position, play_by_play_lines)
        other_player.jump(game, temp_position, play_by_play_lines)

    def check_for_share_space(self, game):
        space_mates = []
        for other_player in game.players:
            if other_player != self and other_player.position == self.position and not other_player.finished:
                space_mates.append(other_player)
        return space_mates
    
    def post_turn_actions(self, game, other_player, play_by_play_lines):
        pass
    
    def trigger_on_main_move_roll(self, roller, game, roll, play_by_play_lines):
        """Called immediately after a player's main roll, before modifications."""
        pass
    
    def register_ability_use(self, game, play_by_play_lines, description=None):
        """Records that an ability was used by this character, with improved tracking."""
        # Ensure ability_activations attribute exists
        if not hasattr(self, 'ability_activations'):
            self.ability_activations = 0
        
        # Ensure recursion tracking exists
        if not hasattr(game, '_recursion_depths'):
            game._recursion_depths = {'ability': 0}
            game._max_recursion_depth = 5
        
        # Guard against excessive recursion
        if game._recursion_depths.get('ability', 0) >= game._max_recursion_depth:
            play_by_play_lines.append(
                f"WARNING: Maximum ability recursion depth reached for {self.name} ({self.piece})! Stopping recursion."
            )
            return
        
        # Increment recursion counter
        game._recursion_depths['ability'] = game._recursion_depths.get('ability', 0) + 1
        
        try:
            # Increment the ability activation counter
            self.ability_activations += 1
            
            # Add detailed tracking message to play-by-play
            if description:
                play_by_play_lines.append(f"{self.name} ({self.piece}) used ability: {description}")
            
            # Trigger Scoocher movement (avoid recursion with Scoocher's own ability)
            if self.piece != "Scoocher":
                game.trigger_scoocher(play_by_play_lines)
        finally:
            # Decrement recursion counter
            game._recursion_depths['ability'] = game._recursion_depths.get('ability', 0) - 1