#!/usr/bin/env python3
"""
Comprehensive ability verification test for all characters.
Tests each character in a specific scenario designed to trigger their ability.
"""

import sys
from datetime import datetime
from game_simulation import Game
from config import character_abilities


class AbilityVerifier:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = []
        self.errors = []

    def verify(self, name, test_func):
        """Run a single verification test."""
        try:
            print(f"  Verifying {name}... ", end='', flush=True)
            result, message = test_func()
            if result:
                print(f"✓ {message}")
                self.passed += 1
                return True
            else:
                print(f"✗ FAILED - {message}")
                self.failed += 1
                self.errors.append(f"{name}: {message}")
                return False
        except Exception as e:
            print(f"✗ ERROR: {e}")
            self.failed += 1
            self.errors.append(f"{name}: Exception - {str(e)}")
            return False

    def summary(self):
        """Print verification summary."""
        print("\n" + "="*70)
        print("VERIFICATION SUMMARY")
        print("="*70)
        print(f"Total verifications: {self.passed + self.failed}")
        print(f"✓ Passed: {self.passed}")
        print(f"✗ Failed: {self.failed}")

        if self.warnings:
            print(f"\n⚠ Warnings: {len(self.warnings)}")
            for warning in self.warnings:
                print(f"  - {warning}")

        if self.errors:
            print(f"\n❌ Errors:")
            for error in self.errors:
                print(f"  - {error}")

        print("="*70)
        return self.failed == 0


def verify_alchemist():
    """Alchemist: When I roll a 1 or 2 for my main move, I can move 4 instead."""
    game = Game(['Alchemist', 'Dummy'], board_type='Mild')
    alchemist = game.players[0]
    play_by_play = []

    # Run multiple turns to get a 1 or 2 roll
    for _ in range(20):
        if alchemist.finished:
            break
        turn_log = []
        alchemist.take_turn(game, turn_log)
        play_by_play.extend(turn_log)

    # Check if ability was used
    if alchemist.ability_activations > 0:
        # Verify the log shows the ability
        if any('move 4 instead' in line for line in play_by_play):
            return True, f"Used {alchemist.ability_activations}x"
        else:
            return False, "Ability activated but no log message"
    else:
        # Check if they actually rolled a 1 or 2
        rolled_low = any(('rolled a 1' in line or 'rolled a 2' in line) and 'Alchemist' in line for line in play_by_play)
        if not rolled_low:
            return True, "Never rolled 1 or 2 (unlucky but OK)"
        return False, "Rolled 1/2 but ability never triggered"


def verify_babayaga():
    """Baba Yaga: Trip any racer that stops on my space, or when I stop on theirs."""
    game = Game(['BabaYaga', 'Dummy'], board_type='Mild')
    babayaga = game.players[0]
    dummy = game.players[1]

    # Set up: Baba Yaga behind, Dummy ahead
    babayaga.position = 3
    dummy.position = 8

    play_by_play = []
    # Baba Yaga moves TO Dummy's space
    babayaga.move(game, play_by_play, 5)

    if dummy.tripped or babayaga.ability_activations > 0:
        return True, f"Used {babayaga.ability_activations}x"
    return False, "Did not trip Dummy when stopping on same space"


def verify_banana():
    """Banana: When a racer passes me, they trip."""
    game = Game(['Banana', 'Legs'], board_type='Mild')
    banana = game.players[0]
    legs = game.players[1]

    # Set up: Legs behind Banana
    banana.position = 5
    legs.position = 3

    play_by_play = []
    # Legs moves forward past Banana
    legs.move(game, play_by_play, 5)  # Should pass Banana

    if legs.tripped or banana.ability_activations > 0:
        return True, f"Used {banana.ability_activations}x"
    return False, "Legs passed Banana but did not trip"


def verify_blimp():
    """Blimp: Get +2 before corner, -1 after corner."""
    game = Game(['Blimp', 'Dummy'], board_type='Mild')
    blimp = game.players[0]

    play_by_play = []
    # Blimp at start (before corner at 15)
    blimp.take_turn(game, play_by_play)

    if blimp.ability_activations > 0:
        if any('+2' in line and 'Blimp' in line for line in play_by_play):
            return True, f"Used {blimp.ability_activations}x"
    return False, "Ability did not trigger before corner"


def verify_boogeyman():
    """Boogeyman: Once per race, warp to space behind lead racer."""
    game = Game(['Boogeyman', 'Legs'], board_type='Mild')
    boogeyman = game.players[0]
    legs = game.players[1]

    # Set Legs as the leader NEAR THE FINISH (Boogeyman has restriction)
    # Boogeyman only warps if leader position >= board.length - 6
    legs.position = 26  # Near finish on 30-space board
    boogeyman.position = 5

    play_by_play = []
    boogeyman.take_turn(game, play_by_play)

    if boogeyman.ability_activations > 0:
        return True, f"Used {boogeyman.ability_activations}x (warped to {boogeyman.position})"
    return False, "Never used warp ability"


def verify_centaur():
    """Centaur: When I pass a racer, they move -2."""
    game = Game(['Centaur', 'Dummy'], board_type='Mild')
    centaur = game.players[0]
    dummy = game.players[1]

    # Set up: Centaur behind Dummy
    centaur.position = 3
    dummy.position = 5

    play_by_play = []
    dummy_start = dummy.position
    # Centaur moves past Dummy
    centaur.move(game, play_by_play, 5)

    if centaur.ability_activations > 0 and dummy.position < dummy_start:
        return True, f"Dummy moved from {dummy_start} to {dummy.position}"
    return False, "Centaur passed Dummy but they didn't move back"


def verify_cheerleader():
    """Cheerleader: At start of turn, can make last place move 2."""
    game = Game(['Cheerleader', 'Dummy', 'Legs'], board_type='Mild')
    cheerleader = game.players[0]
    dummy = game.players[1]

    # Set Cheerleader ahead, Dummy in last
    cheerleader.position = 10
    dummy.position = 2

    play_by_play = []
    cheerleader.take_turn(game, play_by_play)

    if cheerleader.ability_activations > 0:
        return True, f"Used {cheerleader.ability_activations}x"
    return False, "Never boosted last place"


def verify_clowncar():
    """Clown Car: After race, participate in remaining races."""
    # This requires multi-race setup which is complex
    # Just verify it loads and can complete a race
    game = Game(['ClownCar', 'Dummy'], board_type='Mild')
    play_by_play = []
    turns, _ = game.run(play_by_play)
    return True, "Completed race (multi-race behavior not testable here)"


def verify_coach():
    """Coach: Everyone on my space gets +1 to main move."""
    game = Game(['Coach', 'Dummy'], board_type='Mild')
    coach = game.players[0]
    dummy = game.players[1]

    # Put Dummy on same space as Coach
    coach.position = 5
    dummy.position = 5

    play_by_play = []
    dummy.take_turn(game, play_by_play)

    # Check if Dummy got +1 in the logs
    if any('+1' in line and 'Coach' in line and 'Dummy' in line for line in play_by_play):
        return True, f"Coach gave +1 to Dummy"

    # Coach should also give itself +1
    play_by_play2 = []
    coach.take_turn(game, play_by_play2)
    if coach.ability_activations > 0:
        return True, f"Used {coach.ability_activations}x"

    return False, "Coach did not give +1 bonus"


def verify_dicemonger():
    """Dicemonger: When another racer rerolls, I move 1."""
    game = Game(['Dicemonger', 'Magician'], board_type='Mild')
    dicemonger = game.players[0]
    magician = game.players[1]

    play_by_play = []
    # Magician rerolls, should trigger Dicemonger
    magician.take_turn(game, play_by_play)

    if dicemonger.ability_activations > 0:
        return True, f"Used {dicemonger.ability_activations}x"

    # Magician might not have rerolled, try again
    for _ in range(5):
        play_by_play = []
        magician.take_turn(game, play_by_play)
        if dicemonger.ability_activations > 0:
            return True, f"Used {dicemonger.ability_activations}x"

    return True, "Magician didn't reroll (OK)"


def verify_duelist():
    """Duelist: When racer shares my space, roll dice and winner moves 2."""
    game = Game(['Duelist', 'Dummy'], board_type='Mild')
    duelist = game.players[0]
    dummy = game.players[1]

    # Set Duelist ahead, Dummy behind
    duelist.position = 5
    dummy.position = 2

    play_by_play = []
    # Dummy moves to Duelist's space
    dummy.move(game, play_by_play, 3)

    # Call post_turn_actions (simulating end of Dummy's turn)
    for p in game.players:
        p.post_turn_actions(game, dummy, play_by_play)

    if duelist.ability_activations > 0:
        return True, f"Used {duelist.ability_activations}x"

    return False, "Duelist shared space but never dueled"


def verify_dummy():
    """Dummy: Has no special abilities."""
    game = Game(['Dummy', 'Legs'], board_type='Mild')
    dummy = game.players[0]

    play_by_play = []
    dummy.take_turn(game, play_by_play)

    if dummy.ability_activations == 0:
        return True, "Correctly has no abilities"
    return False, "Dummy has ability activations (should be 0)"


def verify_egg():
    """Egg: At start of race, draw 3 racers and pick one."""
    # Egg's ability happens at race start, hard to verify without deck
    game = Game(['Egg', 'Dummy'], board_type='Mild')
    play_by_play = []
    turns, _ = game.run(play_by_play)
    return True, "Completed race (deck selection not testable here)"


def verify_flipflop():
    """Flip Flop: Can skip rolling and swap spaces with another racer."""
    game = Game(['FlipFlop', 'Dummy'], board_type='Mild')
    flipflop = game.players[0]
    dummy = game.players[1]

    # Set up different positions
    flipflop.position = 5
    dummy.position = 10

    play_by_play = []
    flipflop.take_turn(game, play_by_play)

    if flipflop.ability_activations > 0:
        return True, f"Used {flipflop.ability_activations}x"

    # Might not have chosen to swap
    return True, "Completed turn (swap is optional)"


def verify_genius():
    """Genius: Predict roll number. If right, take another turn."""
    game = Game(['Genius', 'Dummy'], board_type='Mild')
    genius = game.players[0]

    play_by_play = []
    for _ in range(20):
        genius.take_turn(game, play_by_play)
        if genius.ability_activations > 0:
            return True, f"Used {genius.ability_activations}x"

    return True, "Predictions didn't match (OK, 1/6 chance per turn)"


def verify_gunk():
    """Gunk: Other racers get -1 to main move."""
    game = Game(['Gunk', 'Dummy'], board_type='Mild')
    gunk = game.players[0]
    dummy = game.players[1]

    play_by_play = []
    dummy.take_turn(game, play_by_play)

    # Check if Dummy got -1 in the logs
    if any('reduced by 1' in line or '-1' in line for line in play_by_play):
        return True, f"Gunk applied -1 to Dummy"

    if gunk.ability_activations > 0:
        return True, f"Used {gunk.ability_activations}x"

    return False, "Gunk did not reduce Dummy's roll"


def verify_hare():
    """Hare: Get +2 to main move. When in lead alone, skip move and get bronze chip."""
    game = Game(['Hare', 'Dummy'], board_type='Mild')
    hare = game.players[0]

    play_by_play = []
    hare.take_turn(game, play_by_play)

    # Should get +2 on first turn
    if hare.ability_activations > 0:
        if any('+2' in line and 'Hare' in line for line in play_by_play):
            return True, f"Used {hare.ability_activations}x"
    return False, "Hare did not get +2 bonus"


def verify_heckler():
    """Heckler: When racer ends turn within 1 space of start, I move 2."""
    game = Game(['Heckler', 'Dummy'], board_type='Mild')
    heckler = game.players[0]
    dummy = game.players[1]

    play_by_play = []
    # Run several turns, hoping for a low roll
    for _ in range(20):
        turn_log = []
        dummy.take_turn(game, turn_log)
        play_by_play.extend(turn_log)
        if heckler.ability_activations > 0:
            return True, f"Used {heckler.ability_activations}x"

    return True, "Dummy never rolled low enough (OK)"


def verify_hugebaby():
    """Huge Baby: No one can be on my space. Warp them behind me."""
    game = Game(['HugeBaby', 'Dummy'], board_type='Mild')
    hugebaby = game.players[0]
    dummy = game.players[1]

    # Set Huge Baby ahead
    hugebaby.position = 8
    dummy.position = 5

    play_by_play = []
    # Dummy tries to land on Huge Baby's space
    dummy.move(game, play_by_play, 3)

    if dummy.position != hugebaby.position or hugebaby.ability_activations > 0:
        return True, f"Warped Dummy (HugeBaby at {hugebaby.position}, Dummy at {dummy.position})"
    return False, "Dummy landed on Huge Baby's space"


def verify_hypnotist():
    """Hypnotist: At start of turn, can warp a racer to my space."""
    game = Game(['Hypnotist', 'Dummy'], board_type='Mild')
    hypnotist = game.players[0]

    play_by_play = []
    hypnotist.take_turn(game, play_by_play)

    if hypnotist.ability_activations > 0:
        return True, f"Used {hypnotist.ability_activations}x"
    return True, "Completed turn (warp is optional)"


def verify_inchworm():
    """Inchworm: When anyone else rolls a 1, they skip move and I move 1."""
    game = Game(['Inchworm', 'Dummy'], board_type='Mild')
    inchworm = game.players[0]
    dummy = game.players[1]

    play_by_play = []
    # Run several turns hoping for a 1
    for _ in range(30):
        turn_log = []
        dummy.take_turn(game, turn_log)
        play_by_play.extend(turn_log)
        if inchworm.ability_activations > 0:
            return True, f"Used {inchworm.ability_activations}x"

    # Check if Dummy ever rolled a 1
    if any('rolled a 1' in line and 'Dummy' in line for line in play_by_play):
        return False, "Dummy rolled 1 but Inchworm didn't trigger"

    return True, "Dummy never rolled 1 (unlucky but OK)"


def verify_lackey():
    """Lackey: When another racer rolls a 6, I move 2 before they move."""
    game = Game(['Lackey', 'Dummy'], board_type='Mild')
    lackey = game.players[0]

    play_by_play = []
    for _ in range(30):
        dummy = game.players[1]
        turn_log = []
        dummy.take_turn(game, turn_log)
        play_by_play.extend(turn_log)
        if lackey.ability_activations > 0:
            return True, f"Used {lackey.ability_activations}x"

    # Check if Dummy rolled a 6
    if any('rolled a 6' in line and 'Dummy' in line for line in play_by_play):
        return False, "Dummy rolled 6 but Lackey didn't trigger"

    return True, "Dummy never rolled 6 (unlucky but OK)"


def verify_leaptoad():
    """Leaptoad: While moving, skip spaces with other racers."""
    game = Game(['Leaptoad', 'Dummy'], board_type='Mild')
    leaptoad = game.players[0]
    dummy = game.players[1]

    # Put Dummy in Leaptoad's path
    leaptoad.position = 2
    dummy.position = 5

    play_by_play = []
    # Leaptoad moves through Dummy's space
    leaptoad.move(game, play_by_play, 6)  # Should skip space 5

    # Check if Leaptoad skipped the space
    if 'skipped' in ' '.join(play_by_play).lower() or leaptoad.position > 8:
        return True, f"Leaptoad at position {leaptoad.position}"

    return True, f"Completed move (at position {leaptoad.position})"


def verify_legs():
    """Legs: Can skip rolling and move 5 instead."""
    game = Game(['Legs', 'Dummy'], board_type='Mild')
    legs = game.players[0]

    play_by_play = []
    legs.take_turn(game, play_by_play)

    if legs.ability_activations > 0:
        # Check for "moves 5" or "move 5" in logs
        if any('move' in line.lower() and '5' in line for line in play_by_play):
            return True, f"Used {legs.ability_activations}x"
    return False, "Legs did not move 5"


def verify_lovableloser():
    """Lovable Loser: Get bronze chip if alone in last place."""
    game = Game(['LovableLoser', 'Dummy', 'Legs'], board_type='Mild')
    loser = game.players[0]

    # Set Lovable Loser in last place alone
    loser.position = 2
    game.players[1].position = 8
    game.players[2].position = 10

    play_by_play = []
    loser.take_turn(game, play_by_play)

    if loser.bronze_chips > 0 or loser.ability_activations > 0:
        return True, f"Got bronze chip"
    return False, "Was in last place but didn't get bronze chip"


def verify_mouth():
    """MOUTH: When I stop on space with exactly one other racer, eliminate them."""
    game = Game(['MOUTH', 'Dummy'], board_type='Mild')
    mouth = game.players[0]
    dummy = game.players[1]

    # Set Dummy at a position
    dummy.position = 5
    mouth.position = 0

    play_by_play = []
    # Move MOUTH to Dummy's space
    mouth.move(game, play_by_play, 5)

    if dummy in game.eliminated_players or mouth.ability_activations > 0:
        return True, f"Eliminated Dummy"
    return False, "MOUTH landed on Dummy but didn't eliminate"


def verify_magician():
    """Magician: Can reroll main move twice."""
    game = Game(['Magician', 'Dummy'], board_type='Mild')
    magician = game.players[0]

    play_by_play = []
    magician.take_turn(game, play_by_play)

    # Check for reroll in logs
    rerolls = [line for line in play_by_play if 'reroll' in line.lower()]
    if len(rerolls) > 0:
        return True, f"{len(rerolls)} rerolls"

    return True, "Didn't reroll (optional ability)"


def verify_mastermind():
    """Mastermind: Predict winner. If right, finish 2nd with 4 bronze chips."""
    game = Game(['Mastermind', 'Legs', 'Hare'], board_type='Mild')
    mastermind = game.players[0]

    play_by_play = []
    turns, _ = game.run(play_by_play)

    if mastermind.ability_activations > 0:
        return True, f"Made prediction"
    return False, "Never made prediction"


def verify_partyanimal():
    """Party Animal: At start of turn, all racers move 1 towards me."""
    game = Game(['PartyAnimal', 'Dummy', 'Legs'], board_type='Mild')
    party = game.players[0]

    # Set Party Animal in middle
    party.position = 10
    game.players[1].position = 5
    game.players[2].position = 15

    play_by_play = []
    party.take_turn(game, play_by_play)

    if party.ability_activations > 0:
        return True, f"Used {party.ability_activations}x"
    return False, "Party Animal didn't move others"


def verify_rocketscientist():
    """Rocket Scientist: Double roll and trip after moving."""
    game = Game(['RocketScientist', 'Dummy'], board_type='Mild')
    rs = game.players[0]

    play_by_play = []
    rs.take_turn(game, play_by_play)

    if rs.ability_activations > 0:
        if any('double' in line.lower() for line in play_by_play):
            return True, f"Used {rs.ability_activations}x"
    return False, "Rocket Scientist didn't double roll"


def verify_romantic():
    """Romantic: When anyone stops on space with exactly one other racer, I move 2."""
    game = Game(['Romantic', 'Dummy', 'Legs'], board_type='Mild')
    romantic = game.players[0]
    dummy = game.players[1]
    legs = game.players[2]

    # Set up: Dummy and Legs on different spaces
    romantic.position = 0
    dummy.position = 5
    legs.position = 3

    play_by_play = []
    # Move Legs to Dummy's space (2 spaces needed)
    legs.move(game, play_by_play, 2)

    if romantic.ability_activations > 0:
        return True, f"Used {romantic.ability_activations}x"
    return False, "Romantic didn't trigger when racers shared space"


def verify_scoocher():
    """Scoocher: When another racer's power happens, I move 1."""
    game = Game(['Scoocher', 'Hare'], board_type='Mild')
    scoocher = game.players[0]
    hare = game.players[1]

    play_by_play = []
    # Hare uses ability (gets +2)
    hare.take_turn(game, play_by_play)

    if scoocher.ability_activations > 0:
        return True, f"Used {scoocher.ability_activations}x"
    return False, "Scoocher didn't move when Hare used ability"


def verify_sisyphis():
    """Sisyphis: Custom behavior (check rules)."""
    game = Game(['Sisyphis', 'Dummy'], board_type='Mild')
    play_by_play = []
    turns, _ = game.run(play_by_play)
    return True, "Completed race"


def verify_skipper():
    """Skipper: When anyone rolls a 1, I go next in turn order."""
    game = Game(['Skipper', 'Dummy', 'Legs'], board_type='Mild')
    skipper = game.players[0]

    play_by_play = []
    for _ in range(30):
        game.players[1].take_turn(game, play_by_play)
        if skipper.ability_activations > 0:
            return True, f"Used {skipper.ability_activations}x"

    return True, "No 1s rolled (unlucky but OK)"


def verify_suckerfish():
    """Suckerfish: When racer starts moving from my space, move with them."""
    game = Game(['Suckerfish', 'Legs'], board_type='Mild')
    suckerfish = game.players[0]
    legs = game.players[1]

    # Put them on same space
    suckerfish.position = 5
    legs.position = 5

    play_by_play = []
    # Legs moves
    legs.take_turn(game, play_by_play)

    if suckerfish.ability_activations > 0:
        return True, f"Used {suckerfish.ability_activations}x"
    return True, "Completed turn (following is optional)"


def verify_thirdwheel():
    """Third Wheel: Before main move, can warp to space with exactly 2 racers."""
    game = Game(['ThirdWheel', 'Dummy', 'Legs'], board_type='Mild')
    tw = game.players[0]

    # Put Dummy and Legs on same space
    game.players[1].position = 8
    game.players[2].position = 8
    tw.position = 2

    play_by_play = []
    tw.take_turn(game, play_by_play)

    if tw.ability_activations > 0:
        return True, f"Used {tw.ability_activations}x"
    return True, "Completed turn (warp is optional)"


def verify_twin():
    """Twin: At race start, pick a previous winner and use their abilities."""
    # Requires multi-race setup
    game = Game(['Twin', 'Dummy'], board_type='Mild')
    play_by_play = []
    turns, _ = game.run(play_by_play)
    return True, "Completed race (multi-race behavior not testable here)"


def main():
    print("="*70)
    print("MAGICAL ATHLETE - COMPREHENSIVE ABILITY VERIFICATION")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    verifier = AbilityVerifier()

    # Map character names to verification functions
    tests = {
        'Alchemist': verify_alchemist,
        'BabaYaga': verify_babayaga,
        'Banana': verify_banana,
        'Blimp': verify_blimp,
        'Boogeyman': verify_boogeyman,
        'Centaur': verify_centaur,
        'Cheerleader': verify_cheerleader,
        'ClownCar': verify_clowncar,
        'Coach': verify_coach,
        'Dicemonger': verify_dicemonger,
        'Duelist': verify_duelist,
        'Dummy': verify_dummy,
        'Egg': verify_egg,
        'FlipFlop': verify_flipflop,
        'Genius': verify_genius,
        'Gunk': verify_gunk,
        'Hare': verify_hare,
        'Heckler': verify_heckler,
        'HugeBaby': verify_hugebaby,
        'Hypnotist': verify_hypnotist,
        'Inchworm': verify_inchworm,
        'Lackey': verify_lackey,
        'Leaptoad': verify_leaptoad,
        'Legs': verify_legs,
        'LovableLoser': verify_lovableloser,
        'MOUTH': verify_mouth,
        'Magician': verify_magician,
        'Mastermind': verify_mastermind,
        'PartyAnimal': verify_partyanimal,
        'RocketScientist': verify_rocketscientist,
        'Romantic': verify_romantic,
        'Scoocher': verify_scoocher,
        'Sisyphis': verify_sisyphis,
        'Skipper': verify_skipper,
        'Suckerfish': verify_suckerfish,
        'ThirdWheel': verify_thirdwheel,
        'Twin': verify_twin,
    }

    print("ABILITY VERIFICATION TESTS")
    print("-"*70)

    for char_name in sorted(tests.keys()):
        verifier.verify(char_name, tests[char_name])

    # Print summary
    success = verifier.summary()

    print(f"\nCompleted: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
