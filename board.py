# board.py

class Board:
    def __init__(self, length=30, corner_position=20):
        self.length = length
        self.spaces = [Space("normal") for _ in range(length)]
        self.spaces[corner_position] = Space("corner")
        self.corner_position = corner_position # Stored for Blimp

    def get_space_type(self, position):
        if position >= self.length:
            return "finish"
        return self.spaces[position].space_type

class Space:
    def __init__(self, space_type):
        self.space_type = space_type

    def on_enter(self, player, game, play_by_play_lines):
        if self.space_type == "corner":
            pass  # Placeholder for future corner actions