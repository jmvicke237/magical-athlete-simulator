# game_simulation.py
import random
from config import character_abilities, BOARD_LENGTH, MAX_TURNS, CORNER_POSITION
from characters.base_character import Character
from board import Board

class Game:
    def __init__(self, character_names, board=None, random_turn_order=False):
        self.players = []
        self.board = board or Board(corner_position=CORNER_POSITION)
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

def _run_single_simulation(character_names, random_turn_order):
    play_by_play_lines = []
    game = Game(character_names, random_turn_order=random_turn_order)
    turns, final_placements = game.run(play_by_play_lines)
    return turns, final_placements, play_by_play_lines

def run_simulations(num_simulations, num_players, fixed_characters=None, random_turn_order=False):
    """Run multiple simulations and return statistics."""
    # Redirect print output to capture debug statements
    import io
    import sys
    import traceback
    original_stdout = sys.stdout
    sys.stdout = io.StringIO()
    
    try:
        all_turns = []
        finish_positions = {char: [] for char in character_abilities.keys()}
        ability_activations = {char: [] for char in character_abilities.keys()}
        all_play_by_play = []
        
        for i in range(num_simulations):
            try:
                selected_characters = fixed_characters if fixed_characters else random.sample(list(character_abilities.keys()), num_players)
                game = Game(selected_characters, random_turn_order=random_turn_order)
                play_by_play_lines = []
                turns, final_placements = game.run(play_by_play_lines)
                
                # Get ability statistics
                try:
                    char_ability_stats = game.get_ability_statistics()
                    for char, count in char_ability_stats.items():
                        if char in ability_activations:
                            ability_activations[char].append(count)
                except AttributeError:
                    # Method doesn't exist yet, skip ability stats for now
                    pass
                
                all_turns.append(turns)
                all_play_by_play.extend([f"--- Simulation {i+1} ---"] + play_by_play_lines)
                
                for place, player in final_placements:
                    finish_positions[player.piece].append(int(place[:-2]))
            except RecursionError as re:
                # Special handling for recursion errors to identify problematic characters
                msg = f"Recursion error in simulation {i+1} with characters: {selected_characters}"
                print(msg)
                traceback.print_exc()
                all_play_by_play.extend([f"--- Simulation {i+1} FAILED ---", msg])
                # Skip this simulation but continue with others
                continue
            except Exception as e:
                # Log other errors but continue with remaining simulations
                msg = f"Error in simulation {i+1}: {str(e)}"
                print(msg)
                traceback.print_exc()
                all_play_by_play.extend([f"--- Simulation {i+1} FAILED ---", msg])
                # Skip this simulation but continue with others
                continue
        
        if not all_turns:
            raise ValueError("All simulations failed! Check the logs for details.")
            
        average_turns = sum(all_turns) / len(all_turns) if all_turns else 0
        average_finish_positions = {char: (sum(positions) / len(positions)) if positions else None for char, positions in finish_positions.items()}
        average_ability_activations = {char: (sum(counts) / len(counts)) if counts else 0 for char, counts in ability_activations.items()}
        
        return average_turns, average_finish_positions, all_play_by_play, average_ability_activations
    except Exception as e:
        # Catch any other errors and provide detailed information
        error_msg = f"Error in run_simulations: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return 0, {}, ["SIMULATION ERROR: " + error_msg], {}
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
            
def get_ability_statistics(self):
    """Returns a dictionary with ability activation counts for each character."""
    return {player.piece: getattr(player, 'ability_activations', 0) for player in self.players}