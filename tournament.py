# tournament.py
import random
from config import character_abilities, DEFAULT_BOARD_TYPE
from game_simulation import Game, Board

class Player:
    """Represents a player in the tournament."""
    def __init__(self, name):
        self.name = name
        self.racers = []  # List of racer names the player has drafted
        self.used_racers = []  # List of racers already used in races
        self.points = {
            "gold": 0,
            "silver": 0,
            "bronze": 0
        }
    
    def add_racer(self, racer):
        """Add a racer to the player's team."""
        self.racers.append(racer)
    
    def select_racer(self, racer=None):
        """Select a racer for the current race.
        If a specific racer is provided, use that one.
        Otherwise, let the player choose from remaining racers."""
        if racer and racer in self.racers and racer not in self.used_racers:
            self.used_racers.append(racer)
            return racer
        
        available_racers = [r for r in self.racers if r not in self.used_racers]
        if not available_racers:
            return None
        
        # In an automated simulation, just pick the first available racer
        selected = available_racers[0]
        self.used_racers.append(selected)
        return selected
    
    def total_points(self):
        """Calculate the total points for the player."""
        return self.points["gold"] * 5 + self.points["silver"] * 3 + self.points["bronze"]
    
    def __str__(self):
        return f"{self.name} - Gold: {self.points['gold']}, Silver: {self.points['silver']}, Bronze: {self.points['bronze']}, Total: {self.total_points()}"


class Tournament:
    """Manages a full 4-race tournament."""
    def __init__(self, player_names):
        self.players = [Player(name) for name in player_names]
        self.racer_deck = list(character_abilities.keys())
        self.races_completed = 0
        self.current_race = None
        self.current_race_players = []  # List of (Player, racer_name) tuples
        self.play_by_play = []
        self.race_results = []
    
    def draft_racers(self):
        """Implement the snake draft for racers."""
        # Shuffle the racer deck
        random.shuffle(self.racer_deck)
        
        # Determine how many racers each player should draft (4 racers each)
        racers_per_player = 4
        
        # First draft set - clockwise
        self._draft_round(self.players, racers_per_player // 2)
        
        # Second draft set - counterclockwise
        self._draft_round(list(reversed(self.players)), racers_per_player // 2)
    
    def _draft_round(self, players_in_order, picks_per_player):
        """Handle one round of the draft."""
        # Draw cards for this draft round
        available_racers = [self.racer_deck.pop() for _ in range(len(players_in_order) * 2)]
        
        for _ in range(picks_per_player):
            for player in players_in_order:
                # In an automated simulation, just pick a random racer
                if available_racers:
                    pick = random.choice(available_racers)
                    available_racers.remove(pick)
                    player.add_racer(pick)
    
    def setup_race(self, board_type=DEFAULT_BOARD_TYPE):
        """Set up the next race in the tournament."""
        self.current_race_players = []
        
        # Each player selects a racer
        for player in self.players:
            racer = player.select_racer()
            if racer:
                self.current_race_players.append((player, racer))
        
        # Create the race with the selected racers and specified board type
        racer_names = [racer for _, racer in self.current_race_players]
        self.current_race = Game(racer_names, board_type=board_type)
        
        # Reset play-by-play for this race
        self.play_by_play = []
    
    def run_race(self):
        """Run the current race and distribute points."""
        if not self.current_race:
            raise ValueError("No race has been set up yet.")
        
        # Create a new play-by-play list for this race
        self.play_by_play = []
        
        # Run the race and get results
        _, final_placements = self.current_race.run(self.play_by_play)
        
        # Get the chip statistics from the game
        chip_stats = self.current_race.get_chip_statistics()
        
        # Award points based on gold/silver/bronze chips
        for game_racer in self.current_race.players:
            racer_piece = game_racer.piece
            
            # Find which player owns this racer
            owner = None
            for player, racer_name in self.current_race_players:
                if racer_name == racer_piece:
                    owner = player
                    break
                    
            if owner:
                # Assign gold chips (5 points each)
                owner.points["gold"] += game_racer.gold_chips
                
                # Assign silver chips (3 points each)
                owner.points["silver"] += game_racer.silver_chips
                
                # Assign bronze chips (1 point each)
                owner.points["bronze"] += game_racer.bronze_chips
                
                # Add a report of points earned to the play-by-play
                if game_racer.gold_chips > 0 or game_racer.silver_chips > 0 or game_racer.bronze_chips > 0:
                    points_earned = (game_racer.gold_chips * 5) + (game_racer.silver_chips * 3) + game_racer.bronze_chips
                    self.play_by_play.append(
                        f"Points summary: {owner.name} earned {points_earned} points from {racer_piece} " + 
                        f"(G:{game_racer.gold_chips}, S:{game_racer.silver_chips}, B:{game_racer.bronze_chips})"
                    )
        
        # Store race results
        self.race_results.append({
            "placements": final_placements,
            "play_by_play": self.play_by_play.copy()
        })
        
        self.races_completed += 1
        return final_placements
    
    def determine_next_start_player(self):
        """Determine the start player for the next race based on the rules."""
        if not self.race_results:
            return 0  # First player starts the first race
        
        last_race = self.race_results[-1]
        racers_by_position = {}
        
        # Map finishing positions to racers
        for place, player in last_race["placements"]:
            position = int(place[:-2])  # Extract position number from "1st", "2nd", etc.
            racers_by_position[position] = player.piece
        
        # Find the player who finished furthest behind
        max_position = max(racers_by_position.keys())
        last_place_racer = racers_by_position[max_position]
        
        # Find which player used that racer
        for i, (player, racer) in enumerate(self.current_race_players):
            if racer == last_place_racer:
                return i
        
        # If there's a tie, use the player with the fewest points
        min_points = float('inf')
        min_points_player = 0
        
        for i, player in enumerate(self.players):
            total = player.total_points()
            if total < min_points:
                min_points = total
                min_points_player = i
        
        return min_points_player
    
    def run_tournament(self, board_type=DEFAULT_BOARD_TYPE):
        """Run a full 4-race tournament."""
        # Draft racers
        self.draft_racers()
        
        # Run 4 races
        for _ in range(4):
            self.setup_race(board_type=board_type)
            if self.current_race_players:  # Make sure we have racers
                self.run_race()
        
        # Determine the winner
        winner = max(self.players, key=lambda p: p.total_points())
        return winner, self.players, self.race_results


def run_tournament_simulation(player_names, board_type=DEFAULT_BOARD_TYPE):
    """Run a simulation of a tournament with the given player names."""
    # Redirect print output to capture debug statements
    import io
    import sys
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        tournament = Tournament(player_names)
        winner, all_players, race_results = tournament.run_tournament(board_type=board_type)
        
        # Calculate total points for each player
        player_points = []
        for player in all_players:
            gold_points = player.points["gold"] * 5
            silver_points = player.points["silver"] * 3
            bronze_points = player.points["bronze"] 
            total_points = gold_points + silver_points + bronze_points
            
            player_points.append({
                "name": player.name,
                "gold_chips": player.points["gold"],
                "silver_chips": player.points["silver"],
                "bronze_chips": player.points["bronze"],
                "gold_points": gold_points,
                "silver_points": silver_points,
                "bronze_points": bronze_points,
                "total_points": total_points,
                "racers": player.racers.copy()
            })
        
        # Sort players by total points (descending)
        player_points.sort(key=lambda p: p["total_points"], reverse=True)
        
        # Return the results
        return {
            "winner": str(winner),
            "players": [str(p) for p in all_players],
            "player_details": player_points,
            "race_results": race_results
        }
    finally:
        # Restore stdout
        sys.stdout = original_stdout


if __name__ == "__main__":
    # Example usage
    player_names = ["Player 1", "Player 2", "Player 3", "Player 4"]
    results = run_tournament_simulation(player_names)
    
    print("Tournament Results:")
    print(f"Winner: {results['winner']}")
    print("\nFinal Standings:")
    for p in results["players"]:
        print(p)
    
    print("\nRace Results:")
    for i, race in enumerate(results["race_results"]):
        print(f"\nRace {i+1}:")
        for place, player in race["placements"]:
            print(f"{place}: {player.name} ({player.piece})")