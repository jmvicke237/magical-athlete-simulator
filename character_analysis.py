# character_analysis.py (enhanced version)
import random
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from game_simulation import Game, run_simulations
from config import character_abilities

class CharacterAnalyzer:
    def __init__(self):
        self.character_stats = {}
        self.global_stats = {}
    
    def reset_stats(self):
        """Reset all gathered statistics."""
        self.character_stats = {}
        self.global_stats = {}
    
    def analyze_all_characters(self, num_simulations=100, racer_counts=[3, 4, 5, 6]):
        """Run comprehensive analysis on all characters with fixed ability tracking."""
        self.reset_stats()
        all_characters = list(character_abilities.keys())
        
        # Initialize stats dictionary for each character
        for char in all_characters:
            self.character_stats[char] = {
                'appearances': 0,
                'positions': [],
                'win_count': 0,
                'ability_triggers': [],
                'racer_count_stats': defaultdict(list)
            }
        
        # Track global stats
        self.global_stats = {
            'total_simulations': 0,
            'racer_counts': defaultdict(int),
            'average_turns': 0,
            'total_turns': 0
        }
        
        # Run simulations for each racer count
        for racer_count in racer_counts:
            print(f"Running simulations with {racer_count} racers...")
            
            for i in range(num_simulations):
                if i % 10 == 0:
                    print(f"  Simulation {i}/{num_simulations}")
                
                # Create and run a game with random characters
                selected_chars = random.sample(all_characters, racer_count)
                game = Game(selected_chars, random_turn_order=True)
                
                # Run the simulation
                play_by_play_lines = []
                turns, final_placements = game.run(play_by_play_lines)
                
                # Update global stats
                self.global_stats['total_simulations'] += 1
                self.global_stats['racer_counts'][racer_count] += 1
                self.global_stats['total_turns'] += turns
                
                # Get ability counts (safely)
                ability_counts = {}
                try:
                    ability_counts = game.get_ability_statistics()
                except (AttributeError, Exception) as e:
                    print(f"Error getting ability statistics: {e}")
                
                # Update character stats
                for place, player in final_placements:
                    char = player.piece
                    position = int(place[:-2])  # Convert '1st', '2nd', etc. to integer
                    
                    self.character_stats[char]['appearances'] += 1
                    self.character_stats[char]['positions'].append(position)
                    self.character_stats[char]['racer_count_stats'][racer_count].append(position)
                    
                    if position == 1:
                        self.character_stats[char]['win_count'] += 1
                    
                    # Record ability triggers if available
                    if char in ability_counts:
                        trigger_count = ability_counts[char]
                        self.character_stats[char]['ability_triggers'].append(trigger_count)
        
        # Calculate averages
        self.global_stats['average_turns'] = self.global_stats['total_turns'] / self.global_stats['total_simulations']
        
        # Return processed stats for UI display
        return self.get_character_ranking()
    
    def get_character_ranking(self):
        """Get an ordered list of characters by performance with proper ability calculations."""
        ranking = []
        
        for char, stats in self.character_stats.items():
            if stats['appearances'] > 0:
                win_rate = (stats['win_count'] / stats['appearances']) * 100
                avg_position = sum(stats['positions']) / len(stats['positions']) if stats['positions'] else float('inf')
                median_position = np.median(stats['positions']) if stats['positions'] else float('inf')
                
                # Calculate average ability triggers correctly
                avg_ability_triggers = 0
                if stats['ability_triggers']:
                    avg_ability_triggers = sum(stats['ability_triggers']) / len(stats['ability_triggers'])
                
                ranking.append({
                    'character': char,
                    'appearances': stats['appearances'],
                    'win_rate': win_rate,
                    'avg_position': avg_position,
                    'median_position': median_position,
                    'avg_ability_triggers': avg_ability_triggers,
                    'racer_count_performance': {
                        count: sum(positions) / len(positions) if positions else float('inf')
                        for count, positions in stats['racer_count_stats'].items()
                    }
                })
        
        # Sort by win rate (descending)
        ranking.sort(key=lambda x: (-x['win_rate'], x['avg_position']))
        return ranking
    
    def analyze_character(self, character_name, num_simulations=100, players_per_race=4, cache_results=True):
        # Check if results are cached
        cache_key = f"{character_name}_{num_simulations}_{players_per_race}"
        if cache_key in self.results_cache and cache_results:
            return self.results_cache[cache_key]
        
        # Run the simulations
        average_turns, average_positions, play_by_play, ability_counts, appearance_count, chip_stats, board_type_counts = run_simulations(
            num_simulations, players_per_race, fixed_characters=[character_name], random_turn_order=True
        )
        
        # Get ability activation count from the new data
        ability_triggers = ability_counts.get(character_name, 0)
        
        # Rest of the method remains similar...
        
        results = {
            "character": character_name,
            "average_position": average_positions.get(character_name, None),
            "win_rate": win_rate,
            "position_distribution": position_distribution,
            "move_statistics": move_statistics,
            "ability_triggers": ability_triggers,
            "average_race_turns": average_turns
        }
        
        # Cache the results
        if cache_results:
            self.results_cache[cache_key] = results
        
        return results
        
    def generate_character_report(self, character, num_simulations=50):
        """Generate a human-readable report about a character."""
        # Implementation to create narrative analysis
        # This would support the Character Analysis tab text report
        pass

    def plot_position_distribution(self, character, results):
        """Create a visualization of position distribution for a character."""
        # Implementation to create chart
        # This would support the Character Analysis tab visualizations
        pass