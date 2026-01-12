# power_system.py
"""
Power resolution system for Magical Athlete simulator.

Implements the official rules' power resolution order:
1. Powers triggered by die rolls (current player, board, others in turn order)
2. Current player powers (current player, board, others in turn order)
3. Racetrack powers
4. Other player powers (in turn order)
"""

from enum import Enum, auto


class PowerPhase(Enum):
    """Phases of power resolution per official Magical Athlete rules.

    Powers execute in this order during each turn:
    1. PRE_ROLL - Before rolling the die (Cheerleader, Hypnotist, Party Animal)
    2. DIE_ROLL_TRIGGER - Triggered by the roll value (Inchworm, Skipper, Lackey)
    3. ROLL_MODIFICATION - Modify the roll value (Gunk, Coach, Blimp, Alchemist)
    4. MOVEMENT - During movement execution (standard move, Leaptoad special)
    5. POST_MOVEMENT - After stopping on space (board effects, HugeBaby, Baba Yaga)
    6. OTHER_REACTIONS - Other players react to movement (Romantic, Scoocher)
    7. POST_TURN - End of turn cleanup (Duelist)

    Within each phase, resolution order is:
    1. Current player first
    2. Board effects (if applicable)
    3. Other players in turn order (clockwise)
    """

    PRE_ROLL = auto()           # Before rolling die
    DIE_ROLL_TRIGGER = auto()   # Triggered by roll value (before modifications)
    ROLL_MODIFICATION = auto()  # Modify roll value
    MOVEMENT = auto()           # During movement
    POST_MOVEMENT = auto()      # After landing on space
    OTHER_REACTIONS = auto()    # Other players react
    POST_TURN = auto()          # End of turn

    def __str__(self):
        return self.name

    def description(self):
        """Return a human-readable description of this phase."""
        descriptions = {
            PowerPhase.PRE_ROLL: "Before rolling the die",
            PowerPhase.DIE_ROLL_TRIGGER: "Triggered by roll value (before modifications)",
            PowerPhase.ROLL_MODIFICATION: "Modify roll value",
            PowerPhase.MOVEMENT: "During movement",
            PowerPhase.POST_MOVEMENT: "After landing on space",
            PowerPhase.OTHER_REACTIONS: "Other players react to movement",
            PowerPhase.POST_TURN: "End of turn cleanup"
        }
        return descriptions.get(self, "Unknown phase")


def get_phase_order():
    """Return the phases in execution order."""
    return [
        PowerPhase.PRE_ROLL,
        PowerPhase.DIE_ROLL_TRIGGER,
        PowerPhase.ROLL_MODIFICATION,
        PowerPhase.MOVEMENT,
        PowerPhase.POST_MOVEMENT,
        PowerPhase.OTHER_REACTIONS,
        PowerPhase.POST_TURN
    ]
