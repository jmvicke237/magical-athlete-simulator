# game_simulation.py
import random
from config import character_abilities, BOARD_LENGTH, MAX_TURNS, CORNER_POSITION, BOARD_TYPES, DEFAULT_BOARD_TYPE
from characters.base_character import Character
from board import Board

class Game:
    def __init__(self, character_names, board_type=DEFAULT_BOARD_TYPE, board=None, random_turn_order=False):
        self.players = []
        
        # Handle board creation
        if board:
            self.board = board
        else:
            # If board_type is Random, choose between Mild and Wild
            actual_board_type = board_type
            if board_type == "Random":
                actual_board_type = random.choice(["Mild", "Wild"])
            
            self.board = Board(board_type=actual_board_type, corner_position=CORNER_POSITION)
        
        self.finished_players = []
        self.eliminated_players = []
        self.turn_order = []
        self.current_player_index = 0
        
        # Recursion tracking for different operations
        self._recursion_depths = {
            'scoocher': 0,
            'movement': 0,
            'ability': 0,
            'space_check': 0
        }
        self._max_recursion_depth = 5  # Set a reasonable limit
        
        self._create_players(character_names, random_turn_order)

    def _create_players(self, character_names, random_turn_order):
        for i, name in enumerate(character_names):
            char_class = character_abilities.get(name, Character)
            # Use piece name directly, and a default player name.
            player = char_class(name=f"Player {i+1}", piece=name)
            self.players.append(player)
            self.turn_order.append(i)
        if random_turn_order:
            random.shuffle(self.turn_order)
        for i, player in enumerate(self.players):
            player.player_number = i + 1

    def run(self, play_by_play_lines):
        turns = 0
        
        for player in self.players:
            player.ability_activations = 0
        
        for player in self.players:
            if player.piece == "Mastermind":
                player.make_prediction(self, play_by_play_lines)

        while not self.should_game_end(play_by_play_lines) and turns < MAX_TURNS:
            turns += 1
            play_by_play_lines.append(f"\nTurn {turns}:")

            for _ in range(len(self.players)):
                player = self.current_player
                if not player.finished and player not in self.eliminated_players:
                    player.take_turn(game=self, play_by_play_lines=play_by_play_lines)
                    if self.should_game_end(play_by_play_lines):
                        break
                    for p in self.players:
                        p.post_turn_actions(self, player, play_by_play_lines)
                if self.should_game_end(play_by_play_lines):
                    break
                self.next_player()

        play_by_play_lines.append("The race has ended!")
        
        play_by_play_lines.append("\nAbility Activation Summary:")
        for player in self.players:
            play_by_play_lines.append(f"{player.name} ({player.piece}): {player.ability_activations} ability uses")
            
        play_by_play_lines.append("\nChip Summary:")
        for player in self.players:
            points = (player.gold_chips * 5) + (player.silver_chips * 3) + (player.bronze_chips * 1)
            play_by_play_lines.append(f"{player.name} ({player.piece}): {points} points (Gold: {player.gold_chips}, Silver: {player.silver_chips}, Bronze: {player.bronze_chips})")
        
        final_placements = self.assign_final_placements()
        for place, placed_player in final_placements:
            play_by_play_lines.append(f"{place}: {placed_player.name} ({placed_player.piece})")
        return turns, final_placements

    def next_player(self):
        self.current_player_index = (self.current_player_index + 1) % len(self.turn_order)
        self._scoocher_recursion_depth = 0

    @property
    def current_player(self):
        return self.players[self.turn_order[self.current_player_index]]

    def should_game_end(self, play_by_play_lines):
        if len(self.finished_players) >= 2 or len(self.players) - len(self.finished_players) - len(self.eliminated_players) <= 1:
            return True
        for p in self.players:
            if p.piece == "Mastermind":
                return p.check_prediction(self, play_by_play_lines)
        return False
                
    def finish_player(self, player, play_by_play_lines):
        if not player.finished:
            player.finished = True
            self.finished_players.append(player)
            
            # Award gold or silver chips based on finish position
            if len(self.finished_players) == 1:
                # First place gets a gold chip (5 points)
                player.gold_chips += 1
                play_by_play_lines.append(f"{player.name} ({player.piece}) finished the race in 1st place and received a gold chip!")
            elif len(self.finished_players) == 2:
                # Second place gets a silver chip (3 points)
                player.silver_chips += 1
                play_by_play_lines.append(f"{player.name} ({player.piece}) finished the race in 2nd place and received a silver chip!")
            else:
                play_by_play_lines.append(f"{player.name} ({player.piece}) finished the race!")

    def eliminate_player(self, player, play_by_play_lines):
        if player not in self.eliminated_players:
            self.eliminated_players.append(player)
            play_by_play_lines.append(f"{player.name} ({player.piece}) was eliminated!")

    def assign_final_placements(self):
        placements = []
        for i, player in enumerate(self.finished_players):
            placements.append((f"{i+1}st", player))
        remaining_players = sorted([p for p in self.players if not p.finished and p not in self.eliminated_players], key=lambda x: (-x.position, x.player_number))
        for i, player in enumerate(remaining_players):
            placements.append((f"{len(self.finished_players) + i + 1}st", player))
        for i, player in enumerate(reversed(self.eliminated_players)):
            placements.append((f"{len(self.players) - i}st", player))
        return placements

    def trigger_scoocher(self, play_by_play_lines):
        # Check if we're already too deep in recursive calls
        max_depth = 3
        if self._recursion_depths['scoocher'] >= max_depth:
            play_by_play_lines.append("WARNING: Skipping Scoocher movement to prevent infinite loop")
            return
        
        # Increment recursion counter
        self._recursion_depths['scoocher'] += 1
        
        try:
            for player in self.players:
                if player.piece == "Scoocher" and not player.finished:
                    # Make sure we're not in an infinite movement loop
                    if self._recursion_depths['movement'] <= 2:
                        player.move(self, play_by_play_lines, 1)
                        player.ability_activations += 1
                        play_by_play_lines.append(f"{player.name} ({player.piece}) used ability: Scoocher")
                        play_by_play_lines.append(f"{player.name} (Scoocher) moved 1 space because another player used their ability.")
                    else:
                        play_by_play_lines.append(f"WARNING: Movement limit reached for {player.name} (Scoocher). Skipping to prevent recursion.")
        finally:
            # Decrement recursion counter
            self._recursion_depths['scoocher'] -= 1

    def change_turn_order(self, skipper, play_by_play_lines):
        skipper_index = self.players.index(skipper)
        if (self.current_player_index + 1) % len(self.turn_order) != skipper_index:
            self.turn_order.remove(skipper_index)
            insert_pos = (self.current_player_index + 1) % len(self.turn_order)
            self.turn_order.insert(insert_pos, skipper_index)
            play_by_play_lines.append(f"Player {skipper.player_number} (Skipper) has changed the turn order to go next!")
            self.current_player_index = (insert_pos - 1) % len(self.turn_order)
            
    def get_ability_statistics(self):
        """Returns a dictionary with ability activation counts for each character."""
        return {player.piece: getattr(player, 'ability_activations', 0) for player in self.players}
        
    def get_chip_statistics(self):
        """Returns a dictionary with chip counts for each character."""
        chip_stats = {}
        for player in self.players:
            chip_stats[player.piece] = {
                'gold': player.gold_chips,
                'silver': player.silver_chips,
                'bronze': player.bronze_chips,
                'points': (player.gold_chips * 5) + (player.silver_chips * 3) + (player.bronze_chips * 1)
            }
        return chip_stats

def _run_single_simulation(character_names, board_type=DEFAULT_BOARD_TYPE, random_turn_order=False):
    play_by_play_lines = []
    game = Game(character_names, board_type=board_type, random_turn_order=random_turn_order)
    turns, final_placements = game.run(play_by_play_lines)
    # Add board info to play-by-play
    play_by_play_lines.insert(0, f"Board: {game.board.get_display_name()}")
    return turns, final_placements, play_by_play_lines, game.board.board_type

def run_simulations(num_simulations, num_players, board_type=DEFAULT_BOARD_TYPE, fixed_characters=None, random_turn_order=False):
    """Run multiple simulations and return statistics with proper ability tracking."""
    # Redirect print output to capture debug statements
    import io
    import sys
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        all_turns = []
        finish_positions = {char: [] for char in character_abilities.keys()}
        ability_activations = {char: [] for char in character_abilities.keys()}
        appearance_count = {char: 0 for char in character_abilities.keys()}  # Track appearances
        chip_statistics = {char: [] for char in character_abilities.keys()}  # Track chip statistics
        all_play_by_play = []
        complete_logs = []  # Store full logs for each simulation
        
        # Track board type usage
        board_type_counts = {"Mild": 0, "Wild": 0}
        
        for i in range(num_simulations):
            selected_characters = fixed_characters if fixed_characters else random.sample(list(character_abilities.keys()), num_players)
            
            # Run the simulation with the specified board type
            game = Game(selected_characters, board_type=board_type, random_turn_order=random_turn_order)
            play_by_play_lines = []
            turns, final_placements = game.run(play_by_play_lines)
            
            # Add board info to play-by-play
            play_by_play_lines.insert(0, f"Board: {game.board.get_display_name()}")
            used_board_type = game.board.board_type
            
            # Track which board type was used
            if used_board_type in board_type_counts:
                board_type_counts[used_board_type] += 1
                
            # Count appearances for each character in this race
            for char in selected_characters:
                appearance_count[char] += 1
            
            # Store the complete logs
            complete_logs.append("\n".join(play_by_play_lines))
            
            # Debug output - include ability activation counts
            debug_info = [f"--- Simulation {i+1} ---"]
            debug_info.append(f"Selected characters: {selected_characters}")
            debug_info.append("Ability activations:")
            
            try:
                # Get the game object from the most recent simulation
                current_game = game  # This was the issue - 'game' variable wasn't defined in this scope
                
                # Get ability statistics
                char_ability_stats = current_game.get_ability_statistics()
                
                # Debug output
                debug_info.append("Ability activations:")
                for char, count in char_ability_stats.items():
                    debug_info.append(f"  {char}: {count}")
                    
                # Store for averaging
                for char, count in char_ability_stats.items():
                    if char in ability_activations:
                        ability_activations[char].append(count)
                
                # Get chip statistics
                chip_stats = current_game.get_chip_statistics()
                
                # Debug output
                debug_info.append("Chip statistics:")
                for char, stats in chip_stats.items():
                    debug_info.append(f"  {char}: {stats['points']} points (G:{stats['gold']}, S:{stats['silver']}, B:{stats['bronze']})")
                    
                # Track chip statistics (we'll add it to the return values)
                for char, stats in chip_stats.items():
                    if char not in chip_statistics:
                        chip_statistics[char] = []
                    chip_statistics[char].append(stats)
            except Exception as e:
                debug_info.append(f"Error getting statistics: {str(e)}")
            
            # Add debug info to play-by-play
            all_play_by_play.extend(debug_info)
            all_play_by_play.extend(play_by_play_lines)
            
            all_turns.append(turns)
            
            for place, player in final_placements:
                finish_positions[player.piece].append(int(place[:-2]))
        
        average_turns = sum(all_turns) / num_simulations if all_turns else 0
        average_finish_positions = {char: (sum(positions) / len(positions)) if positions else None for char, positions in finish_positions.items()}
        
        # Calculate average ability activations with debug output
        average_ability_activations = {}
        for char, counts in ability_activations.items():
            if counts:
                avg = sum(counts) / len(counts)
                average_ability_activations[char] = avg
                all_play_by_play.append(f"Average ability uses for {char}: {avg:.2f}")
            else:
                average_ability_activations[char] = 0
                all_play_by_play.append(f"No data for {char} ability uses")
        
        # Calculate average chip statistics
        average_chip_stats = {}
        for char, stats_list in chip_statistics.items():
            if stats_list:
                # Calculate averages for each chip type and points
                total_gold = sum(s['gold'] for s in stats_list)
                total_silver = sum(s['silver'] for s in stats_list)
                total_bronze = sum(s['bronze'] for s in stats_list)
                total_points = sum(s['points'] for s in stats_list)
                num_appearances = len(stats_list)
                
                average_chip_stats[char] = {
                    'gold_avg': total_gold / num_appearances,
                    'silver_avg': total_silver / num_appearances,
                    'bronze_avg': total_bronze / num_appearances,
                    'points_avg': total_points / num_appearances
                }
                
                all_play_by_play.append(f"Average points for {char}: {total_points / num_appearances:.2f}")
            else:
                average_chip_stats[char] = {
                    'gold_avg': 0, 'silver_avg': 0, 'bronze_avg': 0, 'points_avg': 0
                }
        
        # Add character appearance counts to the debug output
        all_play_by_play.append("\nCharacter appearance counts:")
        for char, count in appearance_count.items():
            if count > 0:
                all_play_by_play.append(f"{char}: {count} races")
        
        # Add board type usage statistics
        all_play_by_play.append("\nBoard type usage:")
        for board_type, count in board_type_counts.items():
            if count > 0:
                percentage = (count / num_simulations) * 100
                all_play_by_play.append(f"{board_type} Board: {count} races ({percentage:.1f}%)")
        
        return average_turns, average_finish_positions, all_play_by_play, average_ability_activations, appearance_count, average_chip_stats, board_type_counts
    finally:
        # Restore stdout
        sys.stdout = original_stdout

def write_summary_to_file(filename, num_simulations, num_players, selected_characters, average_turns, average_finish_positions):
    with open(filename, 'w') as file:
        file.write(f"Number of simulations: {num_simulations}\nNumber of players: {num_players}\n")
        if selected_characters:
            file.write(f"Characters used: {', '.join(selected_characters)}\n")
        file.write(f"Average number of turns per game: {average_turns:.2f}\n\nAverage finish position of each character (best to worst):\n")
        sorted_positions = sorted(average_finish_positions.items(), key=lambda x: (x[1] is None, x[1] if x[1] is not None else float('inf')))
        for char, avg_position in sorted_positions:
            file.write(f"{char}: {avg_position:.2f}\n" if avg_position is not None else f"{char}: Did not participate in any simulation\n")

def write_play_by_play_to_file(filename, play_by_play_lines):
    with open(filename, 'w') as file:
        for line in play_by_play_lines:
            file.write(line + '\n')