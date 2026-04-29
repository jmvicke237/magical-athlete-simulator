# spitball.py

import random
from .base_character import Character

class SpitBall(Character):
    """At the end of my turn, I roll a die. Every non-finished racer within
    that many spaces strictly in front of me gets tripped (skips their next
    main move). PartyPooper's reroll-the-6 rule applies to the spit-ball roll.

    The spit fires whether or not a main move happened — per the game rule
    that "before/after main move" powers still trigger when the racer is
    tripped or otherwise has no main move.

    Side movements (winning a Duelist duel, Suckerfish following, Romantic
    reactions, board "move +N" effects) do NOT trigger this. Architecturally,
    that's enforced by hooking post_move_ability, which base.take_turn
    invokes exactly once per turn, and which is never called from move().
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def post_move_ability(self, game, play_by_play_lines):
        if self.finished or self in game.eliminated_players:
            return

        roll = random.randint(1, 6)
        play_by_play_lines.append(
            f"{self.name} ({self.piece}) rolls a spit-ball die: {roll}"
        )
        # PartyPooper's reroll rule applies — its hook moves PP and forces a reroll on a 6.
        while roll == 6 and self._trigger_party_pooper(game, play_by_play_lines):
            roll = random.randint(1, 6)
            play_by_play_lines.append(
                f"  spit-ball die rerolled to {roll}"
            )

        targets = [
            p for p in game.players
            if p is not self
            and not p.finished
            and p not in game.eliminated_players
            and self.position < p.position <= self.position + roll
        ]

        if not targets:
            play_by_play_lines.append(
                f"  No racers within {roll} spaces ahead of {self.name}."
            )
            return

        for target in targets:
            target.trip(game, play_by_play_lines)
            play_by_play_lines.append(
                f"  Tripped {target.name} ({target.piece}) at position {target.position}."
            )
        self.register_ability_use(game, play_by_play_lines, description="SpitBall")
