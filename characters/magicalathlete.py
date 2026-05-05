# magicalathlete.py

from .base_character import Character
from power_system import PowerPhase


class MagicalAthlete(Character):
    """For my main move, I cast a spell instead of moving:
      1: I trip.
      2: Warp the last place racer to me and we move 2.
      3: Racers in the lead move backwards 3.
      4: Move 4 and trip any racers you pass.
      5: Warp to the lead racer.
      6: Move 6 and take another turn.

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
        finished/eliminated).
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
                1: self._spell_self_trip,
                2: self._spell_warp_last_to_me,
                3: self._spell_lead_back_three,
                4: self._spell_move_four_trip_passed,
                5: self._spell_warp_to_lead,
                6: self._spell_move_six_extra_turn,
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

    def _spell_self_trip(self, game, lines):
        if self.tripped:
            lines.append(f"  Spell 1: {self.name} ({self.piece}) is already tripped.")
            return
        self.trip(game, lines)
        lines.append(f"  Spell 1: {self.name} ({self.piece}) trips themselves.")

    def _spell_warp_last_to_me(self, game, lines):
        candidates = self._other_active_racers(game)
        if not candidates:
            lines.append("  Spell 2: no other racers — spell fizzles.")
            return
        last = min(candidates, key=lambda p: p.position)
        lines.append(
            f"  Spell 2: warping last-place {last.name} ({last.piece}) "
            f"to space {self.position}, then we both move 2."
        )
        last.jump(game, self.position, lines)
        self.move(game, lines, 2)
        if not last.finished and last not in game.eliminated_players:
            last.move(game, lines, 2)

    def _spell_lead_back_three(self, game, lines):
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
        names = ", ".join(f"{p.name} ({p.piece})" for p in leaders)
        lines.append(f"  Spell 3: pushing the lead back 3 — {names}.")
        for leader in leaders:
            leader.move(game, lines, -3)

    def _spell_move_four_trip_passed(self, game, lines):
        start = self.position
        lines.append("  Spell 4: move 4 and trip any racers you pass.")
        self.move(game, lines, 4)
        end = self.position
        passed = self.detect_passes(game, start, end)
        for racer in passed:
            if racer.finished or racer in game.eliminated_players:
                continue
            if racer.tripped:
                continue
            racer.trip(game, lines)
            lines.append(
                f"    {racer.name} ({racer.piece}) is tripped (passed by spell)."
            )

    def _spell_warp_to_lead(self, game, lines):
        candidates = self._other_active_racers(game)
        if not candidates:
            lines.append("  Spell 5: no other racers — spell fizzles.")
            return
        leader = max(candidates, key=lambda p: p.position)
        if leader.position <= self.position:
            lines.append(
                f"  Spell 5: nobody ahead of {self.name} — spell fizzles."
            )
            return
        lines.append(
            f"  Spell 5: warping to lead racer {leader.name} ({leader.piece}) "
            f"at space {leader.position}."
        )
        self.jump(game, leader.position, lines)

    def _spell_move_six_extra_turn(self, game, lines):
        lines.append("  Spell 6: move 6 and take another turn.")
        self.move(game, lines, 6)
        if self.finished or self in game.eliminated_players:
            return
        if not hasattr(game, "queued_turns"):
            game.queued_turns = []
        game.queued_turns.append(self)
        lines.append(f"    {self.name} ({self.piece}) gets an extra turn!")

    # ------------------------------------------------------------------

    def _other_active_racers(self, game):
        return [
            p for p in game.players
            if p is not self
            and not p.finished
            and p not in game.eliminated_players
        ]
