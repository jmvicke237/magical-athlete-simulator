# board.py

class Board:
    def __init__(self, board_type="Mild", length=30, corner_position=15):
        self.board_type = board_type
        self.length = length
        self.spaces = [Space("normal") for _ in range(length)]
        self.spaces[corner_position] = Space("corner")
        self.corner_position = corner_position # Stored for Blimp
        
        # Configure Wild board special spaces if needed
        if self.board_type == "Wild":
            self._setup_wild_board()
    
    def _setup_wild_board(self):
        """Configure Wild board special spaces"""
        # Bronze chip spaces
        self.spaces[1] = Space("bronze_chip")
        self.spaces[13] = Space("bronze_chip")
        
        # Trip spaces
        self.spaces[5] = Space("trip")
        self.spaces[17] = Space("trip")
        self.spaces[26] = Space("trip")
        
        # Movement spaces
        self.spaces[7] = Space("move", value=3)
        self.spaces[11] = Space("move", value=1)
        self.spaces[16] = Space("move", value=-4)
        self.spaces[23] = Space("move", value=2)
        self.spaces[24] = Space("move", value=-2)

    def get_space_type(self, position):
        if position >= self.length:
            return "finish"
        return self.spaces[position].space_type
    
    def get_display_name(self):
        """Return a display-friendly name for the board"""
        return f"{self.board_type} Board ({self.length} spaces, corner at {self.corner_position})"

class Space:
    def __init__(self, space_type, value=0):
        self.space_type = space_type
        self.value = value  # Used for movement spaces

    def on_enter(self, player, game, play_by_play_lines):
        """Handle special effects when a player lands on this space"""
        # Import the logger for recursion tracking
        from debug_utils import logger
        
        # Use a separate recursion counter for space effects
        if 'space_check' not in game._recursion_depths:
            game._recursion_depths['space_check'] = 0
        
        # Check if we're in a recursive space effect
        if game._recursion_depths['space_check'] >= game._max_recursion_depth:
            logger.error(f"Maximum space effect recursion depth reached for {player.name} ({player.piece}) on {self.space_type} space!")
            play_by_play_lines.append(f"WARNING: Space effect loop detected! Stopping recursion for {player.name}.")
            return
        
        # Increment space effect recursion counter
        game._recursion_depths['space_check'] += 1
        
        try:
            # Handle different space types
            if self.space_type == "corner":
                pass  # Placeholder for future corner actions
            elif self.space_type == "bronze_chip":
                player.bronze_chips += 1
                play_by_play_lines.append(f"{player.name} ({player.piece}) landed on a bronze chip space and received 1 bronze chip!")
            elif self.space_type == "trip":
                player.tripped = True
                play_by_play_lines.append(f"{player.name} ({player.piece}) landed on a trip space and will skip their next main move!")
            elif self.space_type == "move":
                if self.value != 0:
                    move_text = f"{abs(self.value)} space{'s' if abs(self.value) > 1 else ''} {'forward' if self.value > 0 else 'backward'}"
                    play_by_play_lines.append(f"{player.name} ({player.piece}) landed on a movement space and will move {move_text}!")
                    
                    # Special case for space 11 on Wild board (moves forward 1) with HugeBaby at space 12
                    # This is a known infinite loop case
                    if player.position == 11 and self.value == 1:
                        hugeBaby_at_12 = False
                        for p in game.players:
                            if p.piece == "HugeBaby" and p.position == 12:
                                hugeBaby_at_12 = True
                                logger.warning(f"Detected potential infinite loop: {player.name} at space 11 with HugeBaby at space 12")
                                
                        # If we'd create an infinite loop AND we're already in at least one level of recursion, break the loop
                        if hugeBaby_at_12 and game._recursion_depths['movement'] > 0:
                            logger.warning(f"Breaking potential infinite loop for {player.name} at space 11")
                            play_by_play_lines.append(f"{player.name} ({player.piece}) avoided getting stuck in a loop with HugeBaby!")
                            return
                    
                    # Move the player
                    player.move(game, play_by_play_lines, self.value)
        finally:
            # Decrement space effect recursion counter
            game._recursion_depths['space_check'] -= 1