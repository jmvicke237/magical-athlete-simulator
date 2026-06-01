# board.py

class Board:
    # Sportals portal pairs. Each space appears in exactly one pair so portal
    # ping-pong only needs a one-step recursion guard (the _via_portal flag).
    SPORTALS_PORTAL_PAIRS = [
        (4, 7),
        (8, 12),
        (11, 15),
        (16, 18),
        (17, 22),
        (20, 23),
        (24, 28),
    ]

    def __init__(self, board_type="Mild", length=30, corner_position=15):
        self.board_type = board_type
        self.length = length
        self.spaces = [Space("normal") for _ in range(length)]
        self.spaces[corner_position] = Space("corner")
        self.corner_position = corner_position # Stored for Blimp

        # Configure board-type-specific special spaces.
        if self.board_type == "Wild":
            self._setup_wild_board()
        elif self.board_type == "Sportals":
            self._setup_sportals_board()

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

    def _setup_sportals_board(self):
        """Place a PortalSpace at every endpoint defined in
        SPORTALS_PORTAL_PAIRS. Pairs overwrite the corner space at 15
        when applicable — characters that reference the corner read
        board.corner_position (an int) rather than the space type, so
        Blimp / Gloth / NepoBaby still work."""
        for a, b in self.SPORTALS_PORTAL_PAIRS:
            self.spaces[a] = PortalSpace(b)
            self.spaces[b] = PortalSpace(a)

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
        # Use a separate recursion counter for space effects
        if 'space_check' not in game._recursion_depths:
            game._recursion_depths['space_check'] = 0

        # Bail silently at cap to keep memory bounded under heavy fan-out.
        if game._recursion_depths['space_check'] >= game._max_recursion_depth:
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
                    # HugeBaby's look-ahead in _check_shared_space prevents the
                    # classic Wild-board-position-11 + HugeBaby-at-12 loop.
                    player.move(game, play_by_play_lines, self.value)
        finally:
            # Decrement space effect recursion counter
            game._recursion_depths['space_check'] -= 1


class PortalSpace(Space):
    """Sportals wormhole: stopping on this space warps the player to its
    paired endpoint. Per spec, "using a portal does not trigger abilities
    that rely on stopping/passing keywords (but it would trigger sharing
    a space)" — we use player.jump() for the warp, which doesn't fire
    detect_passes or on_another_player_move. Sharing-a-space detection
    happens via POST_TURN handlers (Duelist, Penguin alt mode), which
    fire after the turn regardless of how the player got to their
    final position.

    Loop prevention: jump() calls on_enter on the destination, which
    would otherwise warp straight back to the source. We set a transient
    player._via_portal flag around the jump so the destination's
    on_enter sees it and bails. Pairs in SPORTALS_PORTAL_PAIRS don't
    overlap, so a single one-step guard is enough.
    """

    def __init__(self, partner_position):
        super().__init__("portal")
        self.partner = partner_position

    def on_enter(self, player, game, play_by_play_lines):
        if getattr(player, "_via_portal", False):
            return  # Just teleported here from the paired portal — no ping-pong.

        if "space_check" not in game._recursion_depths:
            game._recursion_depths["space_check"] = 0
        if game._recursion_depths["space_check"] >= game._max_recursion_depth:
            return

        game._recursion_depths["space_check"] += 1
        try:
            play_by_play_lines.append(
                f"{player.name} ({player.piece}) hits a Sportal at "
                f"{player.position} — warps to {self.partner}!"
            )
            player._via_portal = True
            try:
                player.jump(game, self.partner, play_by_play_lines)
            finally:
                player._via_portal = False
        finally:
            game._recursion_depths["space_check"] -= 1