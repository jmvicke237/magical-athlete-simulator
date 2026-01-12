#!/usr/bin/env python3
"""
Script to add POWER_PHASES declarations to all character files.
"""

import os
import re

# Character to phase mapping
CHARACTER_PHASES = {
    # ROLL_MODIFICATION phase
    'gunk': ['ROLL_MODIFICATION'],
    'coach': ['ROLL_MODIFICATION'],
    'blimp': ['ROLL_MODIFICATION'],
    'alchemist': ['ROLL_MODIFICATION'],
    'hare': ['ROLL_MODIFICATION', 'PRE_ROLL'],  # +2 to roll, but also checks if alone in lead

    # POST_TURN phase
    'duelist': ['POST_TURN'],

    # OTHER_REACTIONS phase (via on_another_player_move or on_being_passed)
    'romantic': ['OTHER_REACTIONS'],
    'scoocher': ['OTHER_REACTIONS'],
    'centaur': [],  # Uses custom move() method
    'banana': [],  # Uses on_being_passed() hook
    'hugebaby': [],  # Uses on_another_player_move() hook
    'babayaga': [],  # Uses on_another_player_move() hook

    # Characters with custom abilities that don't fit standard phases
    'legs': [],  # Can skip rolling, handled in main_roll()
    'magician': [],  # Reroll ability, handled specially
    'dicemonger': [],  # Allows others to reroll
    'genius': [],  # Predict roll ability
    'rocketscientist': [],  # Double roll ability
    'flipflop': [],  # Swap positions
    'heckler': [],  # Uses post_turn_actions
    'suckerfish': [],  # Move with another
    'leaptoad': [],  # Skip occupied spaces, custom move()
    'mouth': [],  # Eliminate on share space
    'loveableloser': ['PRE_ROLL'],  # Check if alone in last
    'egg': [],  # Draw abilities, not a phase power
    'twin': [],  # Copy another racer
    'clowncar': [],  # Participates in all races
    'mastermind': [],  # Prediction mechanic
    'dummy': [],  # No special ability
}

def add_phase_declaration(filepath, character_name, phases):
    """Add POWER_PHASES declaration to a character file."""

    with open(filepath, 'r') as f:
        content = f.read()

    # Check if already has POWER_PHASES
    if 'POWER_PHASES' in content:
        print(f"  ✓ {character_name}: Already has POWER_PHASES")
        return False

    # Check if needs power_system import
    needs_import = 'from power_system import PowerPhase' not in content

    # Build the phase declaration
    if phases:
        phase_set = '{' + ', '.join(f'PowerPhase.{p}' for p in phases) + '}'
    else:
        phase_set = 'set()'

    # Find the class definition
    class_pattern = rf'class\s+{character_name.title()}.*?:\s*\n'
    match = re.search(class_pattern, content, re.IGNORECASE)

    if not match:
        print(f"  ✗ {character_name}: Could not find class definition")
        return False

    # Add import if needed
    if needs_import and phases:
        import_pattern = r'(from \.base_character import Character)\n'
        content = re.sub(
            import_pattern,
            r'\1\nfrom power_system import PowerPhase\n',
            content
        )

    # Add POWER_PHASES after class definition
    insert_pos = match.end()

    # Check if there's already a docstring
    docstring_match = re.match(r'\s*""".*?"""\s*\n', content[insert_pos:], re.DOTALL)
    if docstring_match:
        insert_pos += docstring_match.end()

    # Insert the POWER_PHASES declaration
    indentation = '    '
    phase_line = f'\n{indentation}POWER_PHASES = {phase_set}\n'
    content = content[:insert_pos] + phase_line + content[insert_pos:]

    # Write back
    with open(filepath, 'w') as f:
        f.write(content)

    print(f"  ✓ {character_name}: Added POWER_PHASES = {phase_set}")
    return True

def main():
    chars_dir = 'characters'

    print("Adding POWER_PHASES declarations to character files...")
    print()

    updated_count = 0

    for char_name, phases in sorted(CHARACTER_PHASES.items()):
        filepath = os.path.join(chars_dir, f'{char_name}.py')

        if not os.path.exists(filepath):
            print(f"  ✗ {char_name}: File not found")
            continue

        if add_phase_declaration(filepath, char_name, phases):
            updated_count += 1

    print()
    print(f"Updated {updated_count} character files")

if __name__ == '__main__':
    main()
