#!/usr/bin/env python3
"""
Statistical analysis tool for character abilities.
Runs large-scale simulations and analyzes ability activation patterns
to identify outliers and potential bugs.
"""

import sys
from datetime import datetime
from collections import defaultdict
from game_simulation import run_simulations
from config import character_abilities


def analyze_ability_statistics(num_simulations=500, players_per_race=8):
    """Run simulations and analyze ability activation statistics."""

    print("="*70)
    print("MAGICAL ATHLETE - STATISTICAL ABILITY ANALYSIS")
    print("="*70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print(f"Running {num_simulations} simulations with {players_per_race} players each...")
    print("This will take a minute or two...")
    print()

    # Run simulations with random characters
    avg_turns, avg_positions, _, avg_abilities, appearances, avg_chip_stats, board_counts = run_simulations(
        num_simulations,
        players_per_race,
        board_type='Random',
        fixed_characters=None,  # Random characters
        random_turn_order=True
    )

    print(f"Completed {num_simulations} simulations!")
    print(f"Average turns per race: {avg_turns:.2f}")
    print(f"Board distribution: Mild={board_counts.get('Mild', 0)}, Wild={board_counts.get('Wild', 0)}")
    print()

    # Analyze ability activations
    print("="*70)
    print("ABILITY ACTIVATION ANALYSIS")
    print("="*70)
    print()

    # Collect statistics
    char_stats = []
    for char_name in sorted(character_abilities.keys()):
        if char_name in appearances and appearances[char_name] > 0:
            races = appearances[char_name]
            avg_ability = avg_abilities.get(char_name, 0)
            avg_pos = avg_positions.get(char_name, 0)
            avg_points = avg_chip_stats.get(char_name, {}).get('points_avg', 0)

            char_stats.append({
                'name': char_name,
                'races': races,
                'avg_ability': avg_ability,
                'avg_position': avg_pos,
                'avg_points': avg_points
            })

    # Calculate statistics
    if char_stats:
        ability_values = [s['avg_ability'] for s in char_stats]
        position_values = [s['avg_position'] for s in char_stats]

        mean_ability = sum(ability_values) / len(ability_values)
        mean_position = sum(position_values) / len(position_values)

        # Standard deviation
        variance_ability = sum((x - mean_ability) ** 2 for x in ability_values) / len(ability_values)
        std_ability = variance_ability ** 0.5

        variance_position = sum((x - mean_position) ** 2 for x in position_values) / len(position_values)
        std_position = variance_position ** 0.5

    # Flag outliers
    warnings = []
    errors = []

    print("1. ZERO ABILITY ACTIVATION CHECK")
    print("-" * 70)
    zero_ability_chars = [s for s in char_stats if s['avg_ability'] == 0]
    if zero_ability_chars:
        print("⚠️  Characters with ZERO ability activations:")
        for s in zero_ability_chars:
            print(f"  ✗ {s['name']:<20} - {s['races']} races, 0 ability uses")
            if s['name'] != 'Dummy':  # Dummy is supposed to have no abilities
                errors.append(f"{s['name']}: ZERO ability activations across {s['races']} races")
    else:
        print("✓ All characters have ability activations (except Dummy)")
    print()

    print("2. ABNORMALLY HIGH ABILITY ACTIVATION CHECK")
    print("-" * 70)
    high_threshold = mean_ability + (2 * std_ability)
    high_ability_chars = [s for s in char_stats if s['avg_ability'] > high_threshold]
    if high_ability_chars:
        high_ability_chars.sort(key=lambda x: x['avg_ability'], reverse=True)
        print(f"⚠️  Characters with HIGH ability usage (>{high_threshold:.1f} uses/race):")
        for s in high_ability_chars:
            print(f"  ! {s['name']:<20} - Avg: {s['avg_ability']:.2f} uses/race ({s['races']} races)")
            warnings.append(f"{s['name']}: Very high ability usage ({s['avg_ability']:.2f} uses/race)")
    else:
        print(f"✓ No characters with abnormally high usage (>{high_threshold:.1f})")
    print()

    print("3. PERFORMANCE OUTLIER CHECK")
    print("-" * 70)
    # Check for characters performing way too well
    best_threshold = mean_position - (2 * std_position)
    worst_threshold = mean_position + (2 * std_position)

    best_chars = [s for s in char_stats if s['avg_position'] < best_threshold]
    worst_chars = [s for s in char_stats if s['avg_position'] > worst_threshold]

    if best_chars:
        best_chars.sort(key=lambda x: x['avg_position'])
        print(f"⚠️  Characters performing VERY WELL (avg pos <{best_threshold:.1f}):")
        for s in best_chars:
            print(f"  ⭐ {s['name']:<20} - Avg position: {s['avg_position']:.2f} ({s['races']} races)")
            warnings.append(f"{s['name']}: Exceptionally strong performance (avg pos {s['avg_position']:.2f})")

    if worst_chars:
        worst_chars.sort(key=lambda x: x['avg_position'], reverse=True)
        print(f"⚠️  Characters performing VERY POORLY (avg pos >{worst_threshold:.1f}):")
        for s in worst_chars:
            print(f"  ⬇️  {s['name']:<20} - Avg position: {s['avg_position']:.2f} ({s['races']} races)")
            warnings.append(f"{s['name']}: Exceptionally weak performance (avg pos {s['avg_position']:.2f})")

    if not best_chars and not worst_chars:
        print(f"✓ All characters within normal performance range")
    print()

    print("4. COMPLETE CHARACTER STATISTICS")
    print("-" * 70)
    print(f"{'Character':<20} {'Races':<8} {'Avg Abilities':<15} {'Avg Position':<15} {'Avg Points':<12}")
    print("-" * 70)

    # Sort by average position
    char_stats.sort(key=lambda x: x['avg_position'])

    for s in char_stats:
        # Flag suspicious characters
        flag = ""
        if s['avg_ability'] == 0 and s['name'] != 'Dummy':
            flag = "❌"
        elif s['avg_ability'] > high_threshold:
            flag = "⚠️ "
        elif s['avg_position'] < best_threshold:
            flag = "⭐"
        elif s['avg_position'] > worst_threshold:
            flag = "⬇️ "

        print(f"{flag}{s['name']:<18} {s['races']:<8} {s['avg_ability']:<15.2f} {s['avg_position']:<15.2f} {s['avg_points']:<12.2f}")

    print()
    print("="*70)
    print("SUMMARY")
    print("="*70)
    print(f"Total characters analyzed: {len(char_stats)}")
    print(f"Mean ability activations: {mean_ability:.2f} ± {std_ability:.2f}")
    print(f"Mean finish position: {mean_position:.2f} ± {std_position:.2f}")
    print()

    if errors:
        print(f"❌ ERRORS FOUND: {len(errors)}")
        for error in errors:
            print(f"  - {error}")
        print()
    else:
        print("✓ No critical errors found")
        print()

    if warnings:
        print(f"⚠️  WARNINGS: {len(warnings)}")
        for warning in warnings[:10]:  # Show first 10
            print(f"  - {warning}")
        if len(warnings) > 10:
            print(f"  ... and {len(warnings) - 10} more")
    else:
        print("✓ No warnings")

    print("="*70)
    print(f"Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return len(errors) == 0


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Analyze character ability statistics')
    parser.add_argument('--simulations', type=int, default=500,
                       help='Number of simulations to run (default: 500)')
    parser.add_argument('--players', type=int, default=8,
                       help='Players per race (default: 8)')

    args = parser.parse_args()

    success = analyze_ability_statistics(args.simulations, args.players)
    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
