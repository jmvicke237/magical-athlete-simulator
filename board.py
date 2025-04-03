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
                player.move(game, play_by_play_lines, self.value)