# frontend.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tournament import Tournament, run_tournament_simulation
from config import character_abilities
from game_simulation import Game, run_simulations
from character_analysis import CharacterAnalyzer
from debug_utils import log_exception, get_full_error_message

class MagicalAthleteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Magical Athlete Simulator")
        self.root.geometry("1000x700")
        
        # Initialize character analyzer
        self.character_analyzer = CharacterAnalyzer()
        
        # Create tabs
        self.tab_control = ttk.Notebook(root)
        
        self.tournament_tab = ttk.Frame(self.tab_control)
        self.single_race_tab = ttk.Frame(self.tab_control)
        self.character_stats_tab = ttk.Frame(self.tab_control)
        self.character_analysis_tab = ttk.Frame(self.tab_control)
        
        self.tab_control.add(self.tournament_tab, text="Tournament Simulation")
        self.tab_control.add(self.single_race_tab, text="Single Race Simulation")
        self.tab_control.add(self.character_stats_tab, text="Character Statistics")
        self.tab_control.add(self.character_analysis_tab, text="Character Analysis")
        
        self.tab_control.pack(expand=1, fill="both")
        
        # Setup each tab
        self._setup_tournament_tab()
        self._setup_single_race_tab()
        self._setup_character_stats_tab()
        self._setup_character_analysis_tab()
    
    def _setup_tournament_tab(self):
        # Left panel - Configuration
        left_frame = ttk.LabelFrame(self.tournament_tab, text="Tournament Configuration")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Number of players
        ttk.Label(left_frame, text="Number of Players:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.tournament_players_var = tk.IntVar(value=4)
        ttk.Spinbox(left_frame, from_=2, to=6, textvariable=self.tournament_players_var, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Player names
        self.player_name_entries = []
        for i in range(6):  # Max 6 players
            ttk.Label(left_frame, text=f"Player {i+1} Name:").grid(row=i+1, column=0, padx=5, pady=5, sticky="w")
            entry = ttk.Entry(left_frame, width=20)
            entry.insert(0, f"Player {i+1}")
            entry.grid(row=i+1, column=1, padx=5, pady=5, sticky="w")
            self.player_name_entries.append(entry)
        
        # Run tournament button
        ttk.Button(left_frame, text="Run Tournament", command=self._run_tournament).grid(row=8, column=0, columnspan=2, padx=5, pady=10)
        
        # Right panel - Results
        right_frame = ttk.LabelFrame(self.tournament_tab, text="Tournament Results")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Results display
        self.tournament_results_text = scrolledtext.ScrolledText(right_frame, width=60, height=30)
        self.tournament_results_text.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Configure grid weights
        self.tournament_tab.columnconfigure(0, weight=1)
        self.tournament_tab.columnconfigure(1, weight=3)
        self.tournament_tab.rowconfigure(0, weight=1)
    
    def _setup_single_race_tab(self):
        # Left panel - Configuration
        left_frame = ttk.LabelFrame(self.single_race_tab, text="Race Configuration")
        left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        
        # Number of simulations
        ttk.Label(left_frame, text="Number of Simulations:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.num_simulations_var = tk.IntVar(value=100)
        ttk.Spinbox(left_frame, from_=1, to=1000, textvariable=self.num_simulations_var, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        # Number of racers
        ttk.Label(left_frame, text="Number of Racers:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.num_racers_var = tk.IntVar(value=4)
        ttk.Spinbox(left_frame, from_=2, to=10, textvariable=self.num_racers_var, width=5).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Fixed characters or random
        ttk.Label(left_frame, text="Character Selection:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.char_selection_var = tk.StringVar(value="Random")
        ttk.Combobox(left_frame, values=["Random", "Fixed"], textvariable=self.char_selection_var, width=10).grid(row=2, column=1, padx=5, pady=5, sticky="w")
        
        # Character selection frame (will be populated dynamically)
        self.character_selection_frame = ttk.Frame(left_frame)
        self.character_selection_frame.grid(row=3, column=0, columnspan=2, padx=5, pady=5, sticky="w")
        
        self.char_selection_var.trace_add("write", self._update_character_selection)
        
        # Character selection lists and checkboxes
        self.selected_characters = []
        self.character_checkboxes = []
        
        # Run button
        ttk.Button(left_frame, text="Run Race Simulations", command=self._run_race_simulations).grid(row=4, column=0, columnspan=2, padx=5, pady=10)
        
        # Right panel - Results
        right_frame = ttk.LabelFrame(self.single_race_tab, text="Race Results")
        right_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
        
        # Results display
        self.race_results_text = scrolledtext.ScrolledText(right_frame, width=60, height=30)
        self.race_results_text.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Add export button frame
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill="x", padx=5, pady=5)
        
        # Initialize the export button (disabled until we have data)
        self.export_button = ttk.Button(
            export_frame, 
            text="Export Play-by-Play Log", 
            command=self._export_play_by_play_log,
            state=tk.DISABLED  # Start disabled
        )
        self.export_button.pack(side="right", padx=5)
        
        # Initialize the complete simulation logs attribute
        self.complete_simulation_logs = []
        
        # Store simulation results for character analysis tabs
        self.simulation_results = {
            'average_turns': 0,
            'average_positions': {},
            'ability_activations': {}
        }
        
        # Configure grid weights
        self.single_race_tab.columnconfigure(0, weight=1)
        self.single_race_tab.columnconfigure(1, weight=3)
        self.single_race_tab.rowconfigure(0, weight=1)
        
        # Initialize character selection
        self._update_character_selection()
        
    def _export_play_by_play_log(self):
        """Export the complete play-by-play logs to a text file."""
        # Check if there are logs to export
        if not hasattr(self, 'complete_simulation_logs') or not self.complete_simulation_logs:
            messagebox.showinfo("Export Log", "No simulation logs to export. Please run a simulation first.")
            return
        
        # Get file path from user
        from datetime import datetime
        default_filename = f"race_sim_complete_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        file_path = tk.filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
            initialfile=default_filename,
            title="Save Complete Play-by-Play Logs"
        )
        
        if not file_path:  # User cancelled
            return
        
        try:
            # Build a formatted log with clear separation between simulations
            full_log = []
            current_sim = []
            sim_number = 0
            
            for line in self.complete_simulation_logs:
                if line.startswith("--- Simulation"):
                    # Start of new simulation
                    if current_sim:
                        # Add the previous simulation with header
                        full_log.append(f"\n{'='*80}\n")
                        full_log.append(f"SIMULATION {sim_number}\n")
                        full_log.append(f"{'='*80}\n\n")
                        full_log.extend(current_sim)
                    
                    # Extract simulation number
                    try:
                        sim_number = int(line.split("---")[1].strip().split(" ")[1])
                    except (IndexError, ValueError):
                        sim_number += 1
                    
                    # Reset for new simulation
                    current_sim = []
                else:
                    # Add line to current simulation
                    current_sim.append(line)
            
            # Add the last simulation if there is one
            if current_sim:
                full_log.append(f"\n{'='*80}\n")
                full_log.append(f"SIMULATION {sim_number}\n")
                full_log.append(f"{'='*80}\n\n")
                full_log.extend(current_sim)
            
            # Add a header
            num_sims = len([l for l in self.complete_simulation_logs if l.startswith("--- Simulation")])
            header = [
                "COMPLETE PLAY-BY-PLAY LOGS\n",
                f"{num_sims} Race Simulations\n",
                f"Exported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            ]
            
            # Write content to file
            with open(file_path, 'w') as f:
                f.write("".join(header))
                f.write("\n".join(full_log))
            
            messagebox.showinfo("Export Log", 
                            f"Complete play-by-play logs successfully exported to:\n{file_path}")
        except Exception as e:
            messagebox.showerror("Export Error", 
                            f"An error occurred while exporting the logs:\n{str(e)}")
    
    def _setup_character_stats_tab(self):
        # Character statistics tab
        main_frame = ttk.Frame(self.character_stats_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top panel - Controls
        top_frame = ttk.LabelFrame(main_frame, text="Analysis Information")
        top_frame.pack(fill="x", padx=5, pady=5)
        
        info_text = "This tab displays character statistics based on the most recent race simulations."
        ttk.Label(top_frame, text=info_text, wraplength=500).grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        ttk.Button(top_frame, text="View Character Statistics", command=self._generate_character_stats).grid(row=0, column=4, padx=15, pady=5)
        
        # Bottom panel - Results table
        bottom_frame = ttk.LabelFrame(main_frame, text="Character Statistics")
        bottom_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview for character statistics
        self.stats_tree = ttk.Treeview(bottom_frame, 
            columns=("Rank", "Character", "Win Rate", "Avg Position", "Points/Race", 
                    "Ability Triggers", "Appearances"), 
            show="headings")
        self.stats_tree.heading("Rank", text="Rank", command=lambda: self._sort_treeview("Rank", False))
        self.stats_tree.heading("Character", text="Character", command=lambda: self._sort_treeview("Character", False))
        self.stats_tree.heading("Win Rate", text="Win Rate", command=lambda: self._sort_treeview("Win Rate", True))
        self.stats_tree.heading("Avg Position", text="Avg Position", command=lambda: self._sort_treeview("Avg Position", False))
        self.stats_tree.heading("Points/Race", text="Points/Race", command=lambda: self._sort_treeview("Points/Race", True))
        self.stats_tree.heading("Ability Triggers", text="Ability Triggers", command=lambda: self._sort_treeview("Ability Triggers", True))
        self.stats_tree.heading("Appearances", text="Appearances", command=lambda: self._sort_treeview("Appearances", True))
                
        self.stats_tree.column("Rank", width=50)
        self.stats_tree.column("Character", width=150)
        self.stats_tree.column("Win Rate", width=100)
        self.stats_tree.column("Avg Position", width=100)
        self.stats_tree.column("Points/Race", width=100)
        self.stats_tree.column("Ability Triggers", width=100)
        self.stats_tree.column("Appearances", width=100)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(bottom_frame, orient="vertical", command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
    
    def _update_character_selection(self, *args):
        # Clear the frame
        for widget in self.character_selection_frame.winfo_children():
            widget.destroy()
        
        self.character_checkboxes = []
        
        if self.char_selection_var.get() == "Fixed":
            # Show character selection checkboxes
            all_characters = sorted(list(character_abilities.keys()))
            num_columns = 4
            
            for i, character in enumerate(all_characters):
                row, col = divmod(i, num_columns)
                var = tk.BooleanVar(value=False)
                chk = ttk.Checkbutton(self.character_selection_frame, text=character, variable=var)
                chk.grid(row=row, column=col, sticky="w", padx=5, pady=2)
                self.character_checkboxes.append((character, var))
    
    def _run_tournament(self):
        # Get number of players
        num_players = self.tournament_players_var.get()
        
        # Get player names
        player_names = [self.player_name_entries[i].get() for i in range(num_players)]
        
        # Clear results
        self.tournament_results_text.delete(1.0, tk.END)
        self.tournament_results_text.insert(tk.END, "Running tournament simulation...\n\n")
        self.root.update()
        
        # Run tournament in a separate thread
        def run_tournament_thread():
            try:
                results = run_tournament_simulation(player_names)
                
                # Display results
                self.root.after(0, lambda: self._display_tournament_results(results))
            except Exception as error:
                # Log the full exception
                error_details = log_exception(error, "tournament simulation")
                error_msg = str(error)
                
                # Show detailed error message - FIXED LAMBDA
                # Pass both variables as default arguments to the lambda function
                self.root.after(0, lambda error_msg=error_msg, details=error_details: 
                            self._show_detailed_error(error_msg, "tournament simulation", details))
        
        threading.Thread(target=run_tournament_thread).start()
    
    def _display_tournament_results(self, results):
        self.tournament_results_text.delete(1.0, tk.END)
        
        # Display winner
        self.tournament_results_text.insert(tk.END, "Tournament Results:\n")
        self.tournament_results_text.insert(tk.END, f"Winner: {results['winner']}\n\n")
        
        # Display final standings using the detailed info
        self.tournament_results_text.insert(tk.END, "Final Standings:\n")
        
        # Use the detailed player information
        if "player_details" in results:
            for player in results["player_details"]:
                name = player["name"]
                gold = player["gold_chips"]
                silver = player["silver_chips"]
                bronze = player["bronze_chips"]
                total = player["total_points"]
                
                # Create a more detailed display
                self.tournament_results_text.insert(tk.END, 
                    f"{name}: {total} points (Gold: {gold} = {gold*5} pts, " + 
                    f"Silver: {silver} = {silver*3} pts, Bronze: {bronze} = {bronze} pts)\n")
                
                # Display the racers each player drafted
                if "racers" in player:
                    racer_list = ", ".join(player["racers"])
                    self.tournament_results_text.insert(tk.END, f"  Drafted: {racer_list}\n")
        else:
            # Fallback to the old format if detailed info not available
            for p in results["players"]:
                self.tournament_results_text.insert(tk.END, f"{p}\n")
        
        # Display race results
        for i, race in enumerate(results["race_results"]):
            self.tournament_results_text.insert(tk.END, f"\nRace {i+1}:\n")
            for place, player in race["placements"]:
                self.tournament_results_text.insert(tk.END, f"{place}: {player.name} ({player.piece})\n")
            
            # Display a sample of the play-by-play, emphasizing point scoring
            self.tournament_results_text.insert(tk.END, "\nPlay-by-Play Highlights:\n")
            
            # Show the points summary lines first if they exist
            point_summary_lines = [line for line in race["play_by_play"] if line.startswith("Points summary:")]
            if point_summary_lines:
                for line in point_summary_lines:
                    self.tournament_results_text.insert(tk.END, f"{line}\n")
                self.tournament_results_text.insert(tk.END, "\n")
            
            # Then show regular play-by-play highlights
            regular_lines = [line for line in race["play_by_play"] if not line.startswith("Points summary:")]
            play_by_play_sample = regular_lines[:15]  # Show first 15 non-point lines
            for line in play_by_play_sample:
                self.tournament_results_text.insert(tk.END, f"{line}\n")
            
            if len(regular_lines) > 15:
                self.tournament_results_text.insert(tk.END, "...\n")
    
    def _run_race_simulations(self):
        # Get configuration values
        num_simulations = self.num_simulations_var.get()
        num_racers = self.num_racers_var.get()
        
        # Get selected characters
        fixed_characters = None
        if self.char_selection_var.get() == "Fixed":
            fixed_characters = [char for char, var in self.character_checkboxes if var.get()]
            if len(fixed_characters) < num_racers:
                messagebox.showerror("Error", f"Please select at least {num_racers} characters.")
                return
        
        # Clear results
        self.race_results_text.delete(1.0, tk.END)
        self.race_results_text.insert(tk.END, "Running race simulations...\n\n")
        self.root.update()
        
        # Run simulations in a separate thread
        # Fix for the lambda function error in run_simulations_thread method

        def run_simulations_thread():
            try:
                # Updated to handle the additional returns including chip statistics
                average_turns, average_finish_positions, all_play_by_play, ability_activations, appearance_count, chip_stats = run_simulations(
                    num_simulations, num_racers, fixed_characters, random_turn_order=True
                )
                
                # Display results with ability data included
                self.root.after(0, lambda: self._display_race_results(
                    average_turns, average_finish_positions, all_play_by_play, 
                    ability_activations, appearance_count, chip_stats
                ))
            except Exception as e:
                # Fix: Capture the exception message before using it in the lambda
                error_msg = str(e)
                self.root.after(0, lambda error_msg=error_msg: messagebox.showerror("Error", f"An error occurred: {error_msg}"))

        threading.Thread(target=run_simulations_thread).start()
    
    def _display_race_results(self, average_turns, average_finish_positions, all_play_by_play, 
                          ability_activations=None, appearance_count=None, chip_stats=None):
        """Display race simulation results with enhanced ability statistics display."""
        # Store the complete logs for later export
        self.complete_simulation_logs = all_play_by_play.copy() if all_play_by_play else []
        
        # Store the results for character analysis tabs
        self.simulation_results = {
            'average_turns': average_turns,
            'average_positions': average_finish_positions,
            'ability_activations': ability_activations,
            'appearance_count': appearance_count,
            'chip_stats': chip_stats
        }
        
        # Clear the results display
        self.race_results_text.delete(1.0, tk.END)
        
        # Display summary - Simplified version
        self.race_results_text.insert(tk.END, f"Completed {self.num_simulations_var.get()} simulations with {self.num_racers_var.get()} racers each.\n\n")
        self.race_results_text.insert(tk.END, f"Average number of turns per race: {average_turns:.2f}\n\n")
        
        # Calculate average points and ability triggers per race
        # We need to be careful here - we want the total per race, not the sum of all character averages
        total_points_per_race = 0
        total_ability_triggers_per_race = 0
        num_racers = self.num_racers_var.get()
        
        # Method 1: Calculate based on what we know must be true for a race
        # For points: Each race will award exactly one gold (5 pts) and one silver (3 pts) chip
        # Bronze chips vary, but we need to be careful about how we calculate them
        fixed_points_per_race = 8  # One gold (5) + one silver (3)
        
        # For bronze chips, we need to consider only if Hare or LoveableLoser were in the races
        # and how often they got their bronze chips when they appeared
        bronze_points_per_race = 0
        
        # Only Hare and LoveableLoser can get bronze chips
        bronze_chars = ["Hare", "LoveableLoser"]
        
        # Calculate how many bronze points were awarded per race on average
        if chip_stats:
            for char in bronze_chars:
                if char in chip_stats and average_finish_positions.get(char) is not None:
                    # Get appearance count and average bronze chips
                    appearances = appearance_count.get(char, 0)
                    if appearances > 0:
                        # Calculate total bronze chips earned by this character
                        total_bronze = chip_stats[char].get('bronze_avg', 0) * appearances
                        # Distribute across all races
                        bronze_points_per_race += total_bronze / self.num_simulations_var.get()
        
        total_points_per_race = fixed_points_per_race + bronze_points_per_race
        
        # For ability triggers: Calculate correctly based on appearances in races
        if ability_activations and appearance_count:
            total_activations = 0
            num_simulations = self.num_simulations_var.get()
            
            # For each character, calculate their total ability triggers across all races
            for char, avg_activations in ability_activations.items():
                if average_finish_positions.get(char) is not None:
                    appearances = appearance_count.get(char, 0)
                    if appearances > 0:
                        # Total activations for this character across all their appearances
                        total_activations += avg_activations * appearances
            
            # Divide by total number of simulations to get per-race average
            total_ability_triggers_per_race = total_activations / num_simulations
        
        self.race_results_text.insert(tk.END, f"Average points awarded per race: {total_points_per_race:.2f}\n")
        self.race_results_text.insert(tk.END, f"Average ability triggers per race: {total_ability_triggers_per_race:.2f}\n\n")
        
        self.race_results_text.insert(tk.END, "For detailed character statistics, please check the 'Character Statistics' and 'Character Analysis' tabs.\n\n")
        
        # Display sample play-by-play
        self.race_results_text.insert(tk.END, "\nSample Play-by-Play (first simulation):\n")
        
        # Check if we have simulation logs
        start_idx = -1
        for i, line in enumerate(all_play_by_play):
            if line.startswith("--- Simulation 1 ---"):
                start_idx = i + 1
                break
        
        if start_idx >= 0:
            end_idx = start_idx + 50  # Show a reasonable number of lines
            
            for i in range(start_idx, min(end_idx, len(all_play_by_play))):
                self.race_results_text.insert(tk.END, f"{all_play_by_play[i]}\n")
            
            if len(all_play_by_play) > end_idx:
                self.race_results_text.insert(tk.END, "...\n")
        else:
            self.race_results_text.insert(tk.END, "No play-by-play logs available.\n")
        
        # Update the export button state to show logs are available
        if hasattr(self, 'export_button') and self.export_button:
            self.export_button.config(state=tk.NORMAL)
    
    def _generate_character_stats(self):
        """Generate comprehensive character statistics using results from the race tab."""
        # Clear the tree
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Check if race simulations have been run
        if not hasattr(self, 'simulation_results') or not self.simulation_results.get('average_positions'):
            # Show message that user needs to run simulations first
            messagebox.showinfo("No Data Available", 
                           "No race simulation data available. Please run race simulations in the 'Single Race Simulation' tab first.")
            return
        
        # Extract data from the stored simulation results
        average_positions = self.simulation_results.get('average_positions', {})
        ability_activations = self.simulation_results.get('ability_activations', {})
        
        # Create a character ranking from the stored data
        character_ranking = []
        
        # Get appearance counts
        appearance_count = self.simulation_results.get('appearance_count', {})
        
        for char, avg_pos in average_positions.items():
            if avg_pos is not None:
                # Calculate win rate based on gold chips if available
                chip_stats = self.simulation_results.get('chip_stats', {})
                if char in chip_stats and appearance_count.get(char, 0) > 0:
                    # Calculate win rate as percentage of races with gold chips
                    stats = chip_stats[char]
                    appearances = appearance_count[char]
                    gold_per_race = stats.get('gold_avg', 0)
                    win_rate_estimate = (gold_per_race * 100)  # Gold chip = win
                else:
                    # Fallback to position-based approximation if chip stats not available
                    # Lower positions are better, so 1.0 is the best possible position
                    win_rate_estimate = max(0, 100 * (1 / avg_pos if avg_pos > 0 else 0))
                    win_rate_estimate = min(100, win_rate_estimate)  # Cap at 100%
                
                # Get ability triggers
                avg_ability_triggers = ability_activations.get(char, 0)
                
                # Get actual appearance count
                appearances = appearance_count.get(char, 0)
                
                # Get points per race from chip stats
                points_per_race = 0
                if char in self.simulation_results.get('chip_stats', {}):
                    points_per_race = self.simulation_results['chip_stats'][char].get('points_avg', 0)
                
                character_ranking.append({
                    'character': char,
                    'appearances': appearances,
                    'win_rate': win_rate_estimate,
                    'avg_position': avg_pos,
                    'points_per_race': points_per_race,
                    'avg_ability_triggers': avg_ability_triggers
                })
        
        # Sort ranking by average position (ascending)
        character_ranking.sort(key=lambda x: x['avg_position'])
        
        # Update UI with the character ranking
        self._update_stats_display(character_ranking)
        
        # Show message indicating stats are from race simulations
        messagebox.showinfo("Statistics Generated", 
                           f"Character statistics displayed from {self.num_simulations_var.get()} race simulations.")

    def _update_stats_display(self, character_ranking, progress_label=None):
        """Update the character statistics display with results."""
        # Remove the progress label if it exists
        if progress_label:
            progress_label.destroy()
        
        print(f"Displaying character ranking for {len(character_ranking)} characters")
        
        # Make sure the tree is visible
        self.stats_tree.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Insert data
        for i, char_data in enumerate(character_ranking):
            try:
                # Format data for display
                win_rate_str = f"{char_data['win_rate']:.1f}%"
                avg_pos_str = f"{char_data['avg_position']:.2f}"
                points_per_race_str = f"{char_data.get('points_per_race', 0):.2f}"
                triggers_str = f"{char_data.get('avg_ability_triggers', 0):.1f}"
                
                # Insert into tree
                self.stats_tree.insert("", "end", values=(
                    i+1, 
                    char_data['character'], 
                    win_rate_str, 
                    avg_pos_str,
                    points_per_race_str,
                    triggers_str,
                    char_data.get('appearances', 0)
                ))
                print(f"Added row for {char_data['character']}")
            except Exception as e:
                print(f"Error displaying character {char_data.get('character', '?')}: {e}")
        
        # Make sure everything is visible
        self.character_stats_tab.update()
        
        # Scroll to the top for visibility
        if self.stats_tree.get_children():
            self.stats_tree.see(self.stats_tree.get_children()[0])
    
    def _display_character_ranking(self, character_ranking, progress_window=None):
        """Display character ranking in the treeview."""
        # Close progress window if provided
        if progress_window:
            progress_window.destroy()
        
        print(f"Displaying character ranking for {len(character_ranking)} characters")
        
        # Clear the tree
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Insert data
        for i, char_data in enumerate(character_ranking):
            try:
                # Format data for display
                win_rate_str = f"{char_data['win_rate']:.1f}%"
                avg_pos_str = f"{char_data['avg_position']:.2f}"
                
                # Check if we have the expected fields
                points_per_race_str = f"{char_data.get('points_per_race', 0):.2f}"
                triggers_str = f"{char_data.get('avg_ability_triggers', 0):.1f}"
                
                # Insert into tree
                self.stats_tree.insert("", "end", values=(
                    i+1, 
                    char_data['character'], 
                    win_rate_str, 
                    avg_pos_str,
                    points_per_race_str,
                    triggers_str,
                    char_data.get('appearances', 0)
                ))
                print(f"Added row for {char_data['character']}")
            except Exception as e:
                print(f"Error displaying character {char_data.get('character', '?')}: {e}")
        self.stats_tree.update()
        self.character_stats_tab.update()
        if self.stats_tree.get_children():
            self.stats_tree.see(self.stats_tree.get_children()[0])

    # Add a helper for progress windows
    def _show_progress_window(self, title, message):
        """Show a progress window during long operations."""
        progress_window = tk.Toplevel(self.root)
        progress_window.title(title)
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        ttk.Label(progress_window, text=message, 
                wraplength=380).pack(padx=20, pady=20)
        
        progress = ttk.Progressbar(progress_window, mode="indeterminate")
        progress.pack(padx=20, pady=10, fill="x")
        progress.start()
        
        return progress_window

    def _setup_character_analysis_tab(self):
        """Set up the character analysis tab with detailed character information."""
        # Main frame
        main_frame = ttk.Frame(self.character_analysis_tab)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Top panel - Controls
        top_frame = ttk.LabelFrame(main_frame, text="Character Analysis")
        top_frame.pack(fill="x", padx=5, pady=5)
        
        # Information text
        info_text = "This tab shows detailed analysis for a specific character based on race simulation data."
        ttk.Label(top_frame, text=info_text, wraplength=500).grid(row=0, column=0, columnspan=3, padx=5, pady=5, sticky="w")
        
        # Character selection dropdown
        ttk.Label(top_frame, text="Select Character:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.analysis_character_var = tk.StringVar()
        char_dropdown = ttk.Combobox(top_frame, textvariable=self.analysis_character_var, 
                                     values=sorted(list(character_abilities.keys())), width=20)
        char_dropdown.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        char_dropdown.current(0)  # Set default selection
        
        ttk.Button(top_frame, text="Analyze Character", command=self._run_character_analysis).grid(row=1, column=2, padx=15, pady=5)
        
        # Content panes
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Left side - Report text
        left_frame = ttk.LabelFrame(content_frame, text="Character Report")
        left_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")
        
        self.character_report_text = scrolledtext.ScrolledText(left_frame, width=50, height=30)
        self.character_report_text.pack(padx=5, pady=5, fill="both", expand=True)
        
        # Right side - Visualizations
        right_frame = ttk.LabelFrame(content_frame, text="Visualizations")
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        
        # Canvas for matplotlib figures
        self.plot_frame = ttk.Frame(right_frame)
        self.plot_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Configure grid weights
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        content_frame.rowconfigure(0, weight=1)
    
    def _run_character_analysis(self):
        """Run analysis for the selected character."""
        character = self.analysis_character_var.get()
        
        # Check if race simulations have been run
        if not hasattr(self, 'simulation_results') or not self.simulation_results.get('average_positions'):
            messagebox.showinfo("No Data Available", 
                           "No race simulation data available. Please run race simulations in the 'Single Race Simulation' tab first.")
            return
        
        # Check if the selected character was in the race
        average_positions = self.simulation_results.get('average_positions', {})
        if character not in average_positions or average_positions[character] is None:
            messagebox.showinfo("Character Not Found", 
                           f"{character} did not participate in the most recent race simulations. Please run new simulations including this character.")
            return
        
        # Clear current content
        self.character_report_text.delete(1.0, tk.END)
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        # Extract data for this character
        avg_position = average_positions.get(character, 0)
        ability_activations = self.simulation_results.get('ability_activations', {}).get(character, 0)
        num_simulations = self.num_simulations_var.get()
        
        # Get chip statistics if available
        chip_stats = self.simulation_results.get('chip_stats', {}).get(character, {})
        appearance_count = self.simulation_results.get('appearance_count', {}).get(character, 0)
        
        # Create a simple report
        report = f"Character Analysis: {character}\n"
        report += f"Based on {appearance_count} race appearances across {num_simulations} simulations\n\n"
        report += f"Average Position: {avg_position:.2f}\n"
        report += f"Ability Activations: {ability_activations:.2f} per race\n\n"
        
        # Add chip statistics
        gold_avg = chip_stats.get('gold_avg', 0)
        silver_avg = chip_stats.get('silver_avg', 0)
        bronze_avg = chip_stats.get('bronze_avg', 0)
        points_avg = chip_stats.get('points_avg', 0)
        
        report += f"Average Points: {points_avg:.2f} per race\n"
        report += f"Chip Breakdown per race:\n"
        report += f"  Gold: {gold_avg:.2f} (5 points each)\n"
        report += f"  Silver: {silver_avg:.2f} (3 points each)\n"
        report += f"  Bronze: {bronze_avg:.2f} (1 point each)\n\n"
        
        # Calculate win rate based on gold chips
        win_rate = gold_avg * 100  # Gold chips = wins
        report += f"Win Rate: {win_rate:.1f}%\n\n"
        
        # Add character description based on performance
        if avg_position < 2.0:
            report += f"{character} is an exceptional racer, consistently finishing near the front.\n"
        elif avg_position < 3.0:
            report += f"{character} is a strong competitor, regularly placing in the top half.\n"
        elif avg_position < 4.0:
            report += f"{character} performs around average compared to other racers.\n"
        else:
            report += f"{character} tends to struggle against other competitors.\n"
        
        # Note on ability usage
        if ability_activations > 2:
            report += f"\n{character}'s ability triggers frequently during races."
        elif ability_activations > 0.5:
            report += f"\n{character}'s ability activates occasionally during races."
        else:
            report += f"\n{character}'s ability rarely comes into play during races."
        
        # Display the report
        self.character_report_text.delete(1.0, tk.END)
        self.character_report_text.insert(tk.END, report)
        
        # Create a simple bar chart for the character's stats
        self._display_character_analysis_charts(character, avg_position, ability_activations, win_rate, points_avg, gold_avg, silver_avg, bronze_avg)
    
    def _display_character_analysis_charts(self, character, avg_position, ability_activations, win_rate, 
                                  points_avg=0, gold_avg=0, silver_avg=0, bronze_avg=0):
        """Display charts for character analysis based on simulation data."""
        try:
            # Create performance metrics chart
            fig1 = plt.figure(figsize=(8, 4))
            metrics = ['Avg Position', 'Ability Uses', 'Win Rate (%)', 'Points/Race']
            values = [avg_position, ability_activations, win_rate, points_avg]
            colors = ['blue', 'green', 'orange', 'purple']
            
            # Instead of multiple axes, use a single subplot with normalized data for better comparison
            fig1, ax = plt.subplots(figsize=(10, 5))
            
            # Normalize values for better visual comparison
            max_val = max(1, max(values))  # Ensure at least 1 to avoid division by zero
            normalized_values = [v/max_val for v in values]
            
            # Create bars with consistent height
            bars = ax.bar(metrics, normalized_values, color=colors, alpha=0.7)
            
            # Add value labels with the original values
            for i, (bar, val) in enumerate(zip(bars, values)):
                if i == 2:  # Win rate percentage
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                           f"{val:.1f}%", ha='center', va='bottom')
                else:
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), 
                           f"{val:.2f}", ha='center', va='bottom')
            
            # Create second chart for chip breakdown
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            chip_labels = ['Gold (5 pts)', 'Silver (3 pts)', 'Bronze (1 pt)', 'Total Points']
            chip_values = [gold_avg, silver_avg, bronze_avg, points_avg]
            chip_colors = ['goldenrod', 'silver', 'brown', 'purple']
            
            # Create chip bars
            chip_bars = ax2.bar(chip_labels, chip_values, color=chip_colors, alpha=0.7)
            
            # Add labels
            for bar, val in zip(chip_bars, chip_values):
                ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height(),
                       f"{val:.2f}", ha='center', va='bottom')
                
            ax2.set_title(f"Chip Statistics for {character}")
            ax2.set_xlabel('Chip Type')
            ax2.set_ylabel('Average per Race')
            
            # Set titles and layout
            ax.set_title(f"Performance Metrics for {character}")
            fig1.tight_layout()
            
            ax2.set_title(f"Chip Statistics for {character}")
            fig2.tight_layout()
            
            # Create canvas for the figures
            canvas1 = FigureCanvasTkAgg(fig1, master=self.plot_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            canvas2 = FigureCanvasTkAgg(fig2, master=self.plot_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create comparative chart (character vs average)
            # Using placeholder average values
            fig2 = plt.figure(figsize=(8, 4))
            
            # Calculate actual average position and ability triggers across all characters
            average_positions = self.simulation_results.get('average_positions', {})
            ability_activations_data = self.simulation_results.get('ability_activations', {})
            
            # Calculate average position of all characters
            valid_positions = [pos for pos in average_positions.values() if pos is not None]
            avg_all_positions = sum(valid_positions) / len(valid_positions) if valid_positions else 3.5
            
            # Calculate average ability triggers of all characters
            valid_abilities = [count for count in ability_activations_data.values() if count > 0]
            avg_all_abilities = sum(valid_abilities) / len(valid_abilities) if valid_abilities else 0.5
            
            labels = ['Average Position', 'Ability Triggers']
            char_values = [avg_position, ability_activations]
            avg_values = [avg_all_positions, avg_all_abilities]
            
            x = range(len(labels))
            width = 0.35
            
            plt.bar([i - width/2 for i in x], char_values, width, label=character, color='blue')
            plt.bar([i + width/2 for i in x], avg_values, width, label='Average Character', color='gray')
            
            plt.ylabel('Value')
            plt.title(f'{character} vs Average Character')
            plt.xticks(x, labels)
            plt.legend()
            
            # Add value labels
            for i, v in enumerate(char_values):
                plt.text(i - width/2, v, f"{v:.2f}", ha='center', va='bottom')
            for i, v in enumerate(avg_values):
                plt.text(i + width/2, v, f"{v:.2f}", ha='center', va='bottom')
            
            canvas2 = FigureCanvasTkAgg(fig2, master=self.plot_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating plots: {e}")
            self.character_report_text.insert(tk.END, f"\n\nError creating visualizations: {e}")
            messagebox.showerror("Visualization Error", f"Could not create visualizations: {e}")


    def _sort_treeview(self, col, reverse):
        """Sort the treeview based on a column.
        
        Args:
            col: Column to sort by
            reverse: If True, sort in descending order (larger values first)
        """
        # Get all items from treeview
        data = [(self.stats_tree.set(item, col), item) for item in self.stats_tree.get_children('')]
        
        # Sort the data
        data.sort(reverse=reverse, key=lambda x: self._convert_value(x[0]))
        
        # Rearrange items in sorted order
        for index, (_, item) in enumerate(data):
            # Update rank if sorting by a different column
            if col != "Rank":
                self.stats_tree.set(item, "Rank", str(index + 1))
            self.stats_tree.move(item, '', index)
        
        # Reverse sort next time
        self.stats_tree.heading(col, command=lambda: self._sort_treeview(col, not reverse))
    
    def _convert_value(self, value):
        """Convert string value to appropriate type for sorting."""
        # Try to convert to float first (handles both integer and decimal numbers)
        try:
            # Handle percentage strings
            if '%' in value:
                return float(value.rstrip('%'))
            return float(value)
        except ValueError:
            # Return as string if it can't be converted to float
            return value.lower()  # Case-insensitive string comparison
            
    def _show_detailed_error(self, error_msg, context, error_details):
        """Show a detailed error message with full traceback in a scrollable window."""
        error_window = tk.Toplevel(self.root)
        error_window.title(f"Error in {context}")
        error_window.geometry("800x600")
        
        # Add a brief explanation
        ttk.Label(error_window, text=f"An error occurred in {context}:", 
                 font=("Arial", 12, "bold")).pack(padx=10, pady=10, anchor="w")
        
        ttk.Label(error_window, text=str(error_msg), 
                 font=("Arial", 10)).pack(padx=10, pady=5, anchor="w")
        
        ttk.Label(error_window, text="Detailed traceback:", 
                 font=("Arial", 12, "bold")).pack(padx=10, pady=10, anchor="w")
        
        # Create scrollable text area for the traceback
        error_text = scrolledtext.ScrolledText(error_window, width=90, height=25)
        error_text.pack(padx=10, pady=5, fill="both", expand=True)
        error_text.insert(tk.END, error_details)
        error_text.config(state="disabled")  # Make it read-only
        
        # Add a close button
        ttk.Button(error_window, text="Close", command=error_window.destroy).pack(pady=10)
        
        # Bring window to front
        error_window.lift()
        error_window.focus_force()


def main():
    root = tk.Tk()
    app = MagicalAthleteApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()