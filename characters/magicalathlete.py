# magicalathlete.py

import random

from .base_character import Character
from power_system import PowerPhase


class MagicalAthlete(Character):
    """For my main move, I cast a spell instead of moving:
      1: I get 1 point.
      2: The last place racer warps to my space, then I move 2.
      3: The lead racer moves backwards 3.
      4: I move 4 and take an extra turn.
      5: I warp to any other racer.
      6: I move 6 and trip any racers I pass.

    Implementation: take_turn override bypasses the normal MOVEMENT phase
    and dispatches to a spell. PRE_ROLL still fires (Cheerleader / Hypnotist
    can target MA), then a fresh d6 is rolled via base.main_roll (so
    PartyPooper still re-rolls 6s), DIE_ROLL_TRIGGER fires (Lackey, Skipper,
    Inchworm see the roll), and the matching spell runs. ROLL_MODIFICATION
    is intentionally skipped — Gunk/Coach/Blimp don't change which spell
    fires; the d6 result is the spell selector, not a movement value.

    Edge cases:
      - If MA is tripped, defer to base (skip main move = skip the spell).
      - If MA is ahead of an active Antimag, defer to base for a vanilla
        d6 main move. MA's whole movement is their power, so suppression
        nukes the spell dispatch and they fall back to plain movement.
      - If Inchworm interrupts a 1-roll (sets skip_main_move), the spell
        is suppressed too — thematically Inchworm cuts off the spell.
      - Spells that target other racers gracefully fizzle when no other
        racer is eligible (alone in the race, or every other racer is
        finished/eliminated). Spell 3 also fizzles if MA is the lead
        (no racers ahead to push back).
    """

    POWER_PHASES = set()
    EDITION = "v2"

    def take_turn(self, game, play_by_play_lines):
        if self.tripped or game.is_power_suppressed_for(self):
            super().take_turn(game, play_by_play_lines)
            return
        self._cast_spell_turn(game, play_by_play_lines)

    def _cast_spell_turn(self, game, play_by_play_lines):
        self.turn_start_position = self.position
        self.last_roll = -1
        self.main_move_multiplier = 1

        # PRE_ROLL: other characters' pre-roll buffs/debuffs still apply.
        game.resolve_phase(PowerPhase.PRE_ROLL, self, play_by_play_lines)

        # Roll a d6 (base.main_roll handles PartyPooper re-rolls of 6).
        roll = self.main_roll(game, play_by_play_lines)
        self.last_roll = roll

        # DIE_ROLL_TRIGGER: Lackey, Skipper, Inchworm react to the roll.
        # NOTE: Inchworm setting skip_main_move on MA after a 1-roll is
        # intentionally honored — Inchworm interrupts the spell.
        game.resolve_phase(PowerPhase.DIE_ROLL_TRIGGER, self, play_by_play_lines,
                           context={'roll': roll})
        game._last_main_roll = self.last_roll

        if not self.skip_main_move:
            play_by_play_lines.append(
                f"{self.name} ({self.piece}) casts a spell — rolled {roll}!"
            )
            spell = {
                1: self._spell_gain_point,
                2: self._spell_warp_last_then_move_2,
                3: self._spell_lead_back_3,
                4: self._spell_move_4_extra_turn,
                5: self._spell_warp_to_any,
                6: self._spell_move_6_trip_passed,
            }.get(roll)
            if spell is not None:
                spell(game, play_by_play_lines)
            self.register_ability_use(
                game, play_by_play_lines, description=f"MagicalAthlete spell {roll}"
            )

        game.resolve_phase(PowerPhase.POST_MOVEMENT, self, play_by_play_lines)

        if not game.is_power_suppressed_for(self):
            self.post_move_ability(game, play_by_play_lines)

        game.resolve_phase(PowerPhase.OTHER_REACTIONS, self, play_by_play_lines)
        game.resolve_phase(PowerPhase.POST_TURN, self, play_by_play_lines)

        if self.skip_main_move:
            self.skip_main_move = False

        game.clear_state_history()

    # ------------------------------------------------------------------
    # Spells
    # ------------------------------------------------------------------

    def _spell_gain_point(self, game, lines):
        """Spell 1: gain 1 bronze chip (1 point)."""
        self.bronze_chips += 1
        lines.append(
            f"  Spell 1: {self.name} ({self.piece}) gains 1 bronze chip (1 point)."
        )

    def _spell_warp_last_then_move_2(self, game, lines):
        """Spell 2: warp the last-place racer to MA's space, then MA moves 2.
        The warped racer does NOT move 2 themselves — only MA moves after the
        warp."""
        candidates = self._other_active_racers(game)
        if not candidates:
            lines.append("  Spell 2: no other racers — spell fizzles.")
            return
        last = min(candidates, key=lambda p: p.position)
        lines.append(
            f"  Spell 2: warping last-place {last.name} ({last.piece}) "
            f"to space {self.position}, then {self.name} ({self.piece}) moves 2."
        )
        last.jump(game, self.position, lines)
        self.move(game, lines, 2)

    def _spell_lead_back_3(self, game, lines):
        """Spell 3: the (single) lead racer moves backwards 3. Ties broken
        randomly. Fizzles if MA is the lead."""
        candidates = self._other_active_racers(game)
        if not candidates:
            lines.append("  Spell 3: no other racers — spell fizzles.")
            return
        max_pos = max(p.position for p in candidates)
        if max_pos <= self.position:
            lines.append(
                f"  Spell 3: no racers ahead of {self.name} — spell fizzles."
            )
            return
        leaders = [p for p in candidates if p.position == max_pos]
        leader = random.choice(leaders)
        lines.append(
            f"  Spell 3: pushing lead racer {leader.name} ({leader.piece}) back 3."
        )
        leader.move(game, lines, -3)

    def _spell_move_4_extra_turn(self, game, lines):
        """Spell 4: move 4 spaces, then queue an extra turn for MA. Bonus
        turn fires through the normal Game.queued_turns mechanism."""
        lines.append("  Spell 4: move 4 and take an extra turn.")
        self.move(game, lines, 4)
        if self.finished or self in game.eliminated_players:
            return
        if not hasattr(game, "queued_turns"):
            game.queued_turns = []
        game.queued_turns.append(self)
        lines.append(f"    {self.name} ({self.piece}) gets an extra turn!")

    def _spell_warp_to_any(self, game, lines):
        """Spell 5: warp to any other racer's space, picked randomly. No
        bias — caster takes the dice however they fall."""
        candidates = self._other_active_racers(game)
        if not candidates:
            lines.append("  Spell 5: no other racers — spell fizzles.")
            return
        target = random.choice(candidates)
        lines.append(
            f"  Spell 5: warping to {target.name} ({target.piece}) "
            f"at space {target.position}."
        )
        self.jump(game, target.position, lines)

    def _spell_move_6_trip_passed(self, game, lines):
        """Spell 6: move 6 and trip any racers passed during the main-move
        segment. Cap the trip range to the move's intended endpoint
        (start + 6, clamped) so post-on_enter cascades (Sportals warps,
        Wild move-spaces) don't extend the trip range past the original
        main move — matches the same fix applied to Weremouth / Centaur /
        base.move's pass detection."""
        start = self.position
        intended_end = max(0, min(start + 6, game.board.length))
        lines.append("  Spell 6: move 6 and trip any racers passed.")
        self.move(game, lines, 6)
        if self.position == start:
            return  # blocked (e.g., Stickler) — nothing passed
        passed = self.detect_passes(game, start, intended_end)
        for racer in passed:
            if racer.finished or racer in game.eliminated_players:
                continue
            if racer.tripped:
                continue
            racer.trip(game, lines)
            lines.append(
                f"    {racer.name} ({racer.piece}) is tripped (passed by spell)."
            )

    # ------------------------------------------------------------------

    def _other_active_racers(self, game):
        return [
            p for p in game.players
            if p is not self
            and not p.finished
            and p not in game.eliminated_players
        ]
