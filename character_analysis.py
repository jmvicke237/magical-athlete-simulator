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
        """Run comprehensive analysis on all characters with various racer counts."""
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
                
                # Set up monitoring for ability triggers
                game._ability_trigger_count = defaultdict(int)
                
                # Modified trigger_scoocher to track ability usage
                original_trigger_fn = game.trigger_scoocher
                
                def tracked_trigger(play_by_play_lines):
                    # Get the character that triggered the ability
                    # This is a bit tricky since we need stack info, but as a proxy:
                    for player in game.players:
                        if player.piece != "Scoocher":
                            game._ability_trigger_count[player.piece] += 1
                    return original_trigger_fn(play_by_play_lines)
                
                # Replace the function with our tracked version
                game.trigger_scoocher = tracked_trigger
                
                # Run the simulation
                play_by_play_lines = []
                turns, final_placements = game.run(play_by_play_lines)
                
                # Update global stats
                self.global_stats['total_simulations'] += 1
                self.global_stats['racer_counts'][racer_count] += 1
                self.global_stats['total_turns'] += turns
                
                # Update character stats
                for place, player in final_placements:
                    char = player.piece
                    position = int(place[:-2])  # Convert '1st', '2nd', etc. to integer
                    
                    self.character_stats[char]['appearances'] += 1
                    self.character_stats[char]['positions'].append(position)
                    self.character_stats[char]['racer_count_stats'][racer_count].append(position)
                    
                    if position == 1:
                        self.character_stats[char]['win_count'] += 1
                    
                    # Record ability triggers
                    trigger_count = game._ability_trigger_count.get(char, 0)
                    self.character_stats[char]['ability_triggers'].append(trigger_count)
        
        # Calculate averages
        self.global_stats['average_turns'] = self.global_stats['total_turns'] / self.global_stats['total_simulations']
        
        # Return processed stats for UI display
        return self.get_character_ranking()
    
    def get_character_ranking(self):
        """Get an ordered list of characters by performance."""
        ranking = []
        
        for char, stats in self.character_stats.items():
            if stats['appearances'] > 0:
                win_rate = (stats['win_count'] / stats['appearances']) * 100
                avg_position = sum(stats['positions']) / len(stats['positions']) if stats['positions'] else float('inf')
                median_position = np.median(stats['positions']) if stats['positions'] else float('inf')
                avg_ability_triggers = sum(stats['ability_triggers']) / len(stats['ability_triggers']) if stats['ability_triggers'] else 0
                
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
    
    def analyze_character(self, character, num_simulations=50):
        """Run detailed analysis on a specific character."""
        # Implementation similar to above but focused on one character
        # This would support the Character Analysis tab
        pass
        
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