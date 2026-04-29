# frontend.py
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from tournament import Tournament, run_tournament_simulation
from config import character_abilities, BOARD_TYPES, DEFAULT_BOARD_TYPE, EDITIONS, DEFAULT_EDITION, get_characters_by_edition
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
        self.character_analysis_tab = ttk.Frame(self.tab_control)

        self.tab_control.add(self.single_race_tab, text="Single Race Simulation")
        self.tab_control.add(self.tournament_tab, text="Tournament Simulation")
        self.tab_control.add(self.character_analysis_tab, text="Character Analysis")

        self.tab_control.pack(expand=1, fill="both")

        # Setup each tab
        self._setup_tournament_tab()
        self._setup_single_race_tab()
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
        
        # Board type selection
        ttk.Label(left_frame, text="Board Type:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.tournament_board_type_var = tk.StringVar(value=DEFAULT_BOARD_TYPE)
        ttk.Combobox(left_frame, values=BOARD_TYPES, textvariable=self.tournament_board_type_var, width=10).grid(row=7, column=1, padx=5, pady=5, sticky="w")

        # Edition selection
        ttk.Label(left_frame, text="Edition:").grid(row=8, column=0, padx=5, pady=5, sticky="nw")
        self.tournament_edition_var = tk.StringVar(value=DEFAULT_EDITION)
        edition_frame = ttk.Frame(left_frame)
        edition_frame.grid(row=8, column=1, padx=5, pady=5, sticky="w")
        for ed in EDITIONS:
            ttk.Radiobutton(edition_frame, text=ed, variable=self.tournament_edition_var, value=ed).pack(anchor="w")

        # Run tournament button
        ttk.Button(left_frame, text="Run Tournament", command=self._run_tournament).grid(row=9, column=0, columnspan=2, padx=5, pady=10)
        
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
        self.num_simulations_var = tk.IntVar(value=10000)
        ttk.Spinbox(left_frame, from_=1, to=100000, textvariable=self.num_simulations_var, width=6).grid(row=0, column=1, padx=5, pady=5, sticky="w")

        # Number of racers
        ttk.Label(left_frame, text="Number of Racers:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.num_racers_var = tk.IntVar(value=5)
        ttk.Spinbox(left_frame, from_=2, to=10, textvariable=self.num_racers_var, width=5).grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Board type selection (checkboxes)
        ttk.Label(left_frame, text="Board Types:").grid(row=2, column=0, padx=5, pady=5, sticky="nw")
        board_frame = ttk.Frame(left_frame)
        board_frame.grid(row=2, column=1, padx=5, pady=5, sticky="w")

        self.board_mild_var = tk.BooleanVar(value=True)
        self.board_wild_var = tk.BooleanVar(value=True)

        ttk.Checkbutton(board_frame, text="Mild", variable=self.board_mild_var).pack(anchor="w")
        ttk.Checkbutton(board_frame, text="Wild", variable=self.board_wild_var).pack(anchor="w")
        
        # Edition selection
        ttk.Label(left_frame, text="Edition:").grid(row=3, column=0, padx=5, pady=5, sticky="nw")
        self.race_edition_var = tk.StringVar(value=DEFAULT_EDITION)
        race_edition_frame = ttk.Frame(left_frame)
        race_edition_frame.grid(row=3, column=1, padx=5, pady=5, sticky="w")
        for ed in EDITIONS:
            ttk.Radiobutton(race_edition_frame, text=ed, variable=self.race_edition_var, value=ed).pack(anchor="w")

        # Fixed characters or random
        ttk.Label(left_frame, text="Character Selection:").grid(row=4, column=0, padx=5, pady=5, sticky="w")
        self.char_selection_var = tk.StringVar(value="Random")
        ttk.Combobox(left_frame, values=["Random", "Fixed"], textvariable=self.char_selection_var, width=10).grid(row=4, column=1, padx=5, pady=5, sticky="w")

        # Character selection frame (will be populated dynamically)
        self.character_selection_frame = ttk.Frame(left_frame)
        self.character_selection_frame.grid(row=5, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        self.char_selection_var.trace_add("write", self._update_character_selection)
        # Re-filter checkbox list when edition changes
        self.race_edition_var.trace_add("write", self._update_character_selection)

        # Character selection lists and checkboxes
        self.selected_characters = []
        self.character_checkboxes = []

        # Prometheus tweaks (only matter if Prometheus is in the race)
        ttk.Label(left_frame, text="Prometheus elim threshold:").grid(row=6, column=0, padx=5, pady=5, sticky="w")
        self.prometheus_threshold_var = tk.IntVar(value=3)
        ttk.Spinbox(left_frame, from_=0, to=30, textvariable=self.prometheus_threshold_var, width=5).grid(row=6, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(left_frame, text="Prometheus starting points:").grid(row=7, column=0, padx=5, pady=5, sticky="w")
        self.prometheus_starting_points_var = tk.IntVar(value=3)
        ttk.Spinbox(left_frame, from_=0, to=30, textvariable=self.prometheus_starting_points_var, width=5).grid(row=7, column=1, padx=5, pady=5, sticky="w")

        ttk.Label(left_frame, text="Prometheus check at:").grid(row=8, column=0, padx=5, pady=5, sticky="nw")
        self.prometheus_check_timing_var = tk.StringVar(value="start")
        check_timing_frame = ttk.Frame(left_frame)
        check_timing_frame.grid(row=8, column=1, padx=5, pady=5, sticky="w")
        ttk.Radiobutton(check_timing_frame, text="Start of turn", variable=self.prometheus_check_timing_var, value="start").pack(anchor="w")
        ttk.Radiobutton(check_timing_frame, text="End of turn", variable=self.prometheus_check_timing_var, value="end").pack(anchor="w")

        # HighRoller riskiness — total threshold to stop rolling. Higher = riskier.
        ttk.Label(left_frame, text="HighRoller stop-at:").grid(row=9, column=0, padx=5, pady=5, sticky="w")
        self.highroller_threshold_var = tk.IntVar(value=8)
        ttk.Spinbox(left_frame, from_=1, to=30, textvariable=self.highroller_threshold_var, width=5).grid(row=9, column=1, padx=5, pady=5, sticky="w")

        # Random starting bronze chips per racer (0-5)
        self.random_starting_bronze_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(left_frame, text="Random starting bronze (0-5 each racer)", variable=self.random_starting_bronze_var).grid(row=10, column=0, columnspan=2, padx=5, pady=5, sticky="w")

        # Run button
        ttk.Button(left_frame, text="Run Race Simulations", command=self._run_race_simulations).grid(row=11, column=0, columnspan=2, padx=5, pady=10)
        
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
    
    def _update_character_selection(self, *args):
        # Clear the frame
        for widget in self.character_selection_frame.winfo_children():
            widget.destroy()

        self.character_checkboxes = []

        if self.char_selection_var.get() == "Fixed":
            # Show character selection checkboxes filtered by edition
            edition = self.race_edition_var.get() if hasattr(self, 'race_edition_var') else DEFAULT_EDITION
            filtered = get_characters_by_edition(edition)
            all_characters = sorted(filtered.keys())
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

        # Get board type
        board_type = self.tournament_board_type_var.get()

        # Get edition and validate pool size (snake draft needs 4 racers per player)
        edition = self.tournament_edition_var.get()
        allowed = list(get_characters_by_edition(edition).keys())
        racers_needed = num_players * 4
        if len(allowed) < racers_needed:
            messagebox.showerror(
                "Not enough racers",
                f"{edition} edition has {len(allowed)} racer(s); a {num_players}-player tournament needs {racers_needed}."
            )
            return

        # Clear results
        self.tournament_results_text.delete(1.0, tk.END)
        self.tournament_results_text.insert(tk.END, f"Running tournament simulation with {board_type} board ({edition} edition)...\n\n")
        self.root.update()

        # Run tournament in a separate thread
        def run_tournament_thread():
            try:
                results = run_tournament_simulation(player_names, board_type=board_type, allowed_characters=allowed)
                
                # Display results
                self.root.after(0, lambda: self._display_tournament_results(results, edition))
            except Exception as error:
                # Log the full exception
                error_details = log_exception(error, "tournament simulation")
                error_msg = str(error)
                
                # Show detailed error message - FIXED LAMBDA
                # Pass both variables as default arguments to the lambda function
                self.root.after(0, lambda error_msg=error_msg, details=error_details: 
                            self._show_detailed_error(error_msg, "tournament simulation", details))
        
        threading.Thread(target=run_tournament_thread).start()
    
    def _display_tournament_results(self, results, edition=None):
        self.tournament_results_text.delete(1.0, tk.END)

        # Display winner
        self.tournament_results_text.insert(tk.END, "Tournament Results:\n")
        self.tournament_results_text.insert(tk.END, f"Winner: {results['winner']}\n\n")

        # Average turns overall + per board type
        race_results = results.get("race_results", [])
        all_turns = [r["turns"] for r in race_results if "turns" in r]
        if all_turns:
            avg_total = sum(all_turns) / len(all_turns)
            self.tournament_results_text.insert(tk.END, f"Average number of turns per race: {avg_total:.2f}\n")
            for bt in ("Mild", "Wild"):
                bt_turns = [r["turns"] for r in race_results if r.get("board_type") == bt and "turns" in r]
                if bt_turns:
                    self.tournament_results_text.insert(tk.END,
                        f"  {bt} board: {sum(bt_turns) / len(bt_turns):.2f}  ({len(bt_turns)} race{'s' if len(bt_turns) != 1 else ''})\n")
                else:
                    self.tournament_results_text.insert(tk.END, f"  {bt} board: —\n")
            self.tournament_results_text.insert(tk.END, "\n")
        
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

        # Push aggregated per-character stats from the 4 races into Character Analysis tab
        ranking = self._build_ranking_from_tournament(results)
        num_races = len(results.get("race_results", []))
        ed_label = edition or "?"
        status = (f"Showing {num_races} races from the latest tournament "
                  f"({ed_label} edition). Click headers to sort.")
        self._populate_analysis_table(ranking, status)

    def _build_ranking_from_tournament(self, results):
        """Aggregate per-character stats across the tournament's races."""
        from collections import defaultdict
        appearances = defaultdict(int)
        wins = defaultdict(int)
        position_sum = defaultdict(int)
        ability_sum = defaultdict(int)
        points_sum = defaultdict(int)

        for race in results.get("race_results", []):
            for place_str, player in race.get("placements", []):
                char = player.piece
                pos = int(place_str[:-2])
                appearances[char] += 1
                position_sum[char] += pos
                if pos == 1:
                    wins[char] += 1
                ability_sum[char] += getattr(player, "ability_activations", 0)
                points_sum[char] += (
                    getattr(player, "gold_chips", 0) * 5
                    + getattr(player, "silver_chips", 0) * 3
                    + getattr(player, "bronze_chips", 0)
                )

        ranking = []
        for char, n in appearances.items():
            ranking.append({
                "character": char,
                "appearances": n,
                "win_rate": (wins[char] / n) * 100,
                "avg_position": position_sum[char] / n,
                "avg_points": points_sum[char] / n,
                "avg_ability_triggers": ability_sum[char] / n,
            })
        ranking.sort(key=lambda x: (-x["win_rate"], x["avg_position"]))
        return ranking

    def _run_race_simulations(self):
        # Get configuration values
        num_simulations = self.num_simulations_var.get()
        num_racers = self.num_racers_var.get()

        # Determine board type from checkboxes
        mild_selected = self.board_mild_var.get()
        wild_selected = self.board_wild_var.get()

        if not mild_selected and not wild_selected:
            messagebox.showerror("Error", "Please select at least one board type.")
            return
        elif mild_selected and wild_selected:
            board_type = "Random"
            board_desc = "Mild and Wild boards (random)"
        elif mild_selected:
            board_type = "Mild"
            board_desc = "Mild board"
        else:  # wild_selected
            board_type = "Wild"
            board_desc = "Wild board"

        # Get edition and the allowed character pool
        edition = self.race_edition_var.get()
        allowed = list(get_characters_by_edition(edition).keys())
        prometheus_threshold = self.prometheus_threshold_var.get()
        prometheus_starting_points = self.prometheus_starting_points_var.get()
        prometheus_check_timing = self.prometheus_check_timing_var.get()
        highroller_threshold = self.highroller_threshold_var.get()
        random_starting_bronze = self.random_starting_bronze_var.get()
        if len(allowed) < num_racers:
            messagebox.showerror(
                "Not enough racers",
                f"{edition} edition has {len(allowed)} racer(s); need at least {num_racers}."
            )
            return

        # Get selected characters
        fixed_characters = None
        if self.char_selection_var.get() == "Fixed":
            fixed_characters = [char for char, var in self.character_checkboxes if var.get()]
            if len(fixed_characters) < num_racers:
                messagebox.showerror("Error", f"Please select at least {num_racers} characters.")
                return

        # Clear results
        self.race_results_text.delete(1.0, tk.END)
        self.race_results_text.insert(tk.END, f"Running race simulations with {board_desc} ({edition} edition)...\n\n")
        self.root.update()
        
        # Run simulations in a separate thread
        # Fix for the lambda function error in run_simulations_thread method

        def run_simulations_thread():
            try:
                # Updated to handle the additional returns including chip statistics and board type counts
                # collect_detailed_logs=True because frontend has an export logs feature
                average_turns, average_finish_positions, all_play_by_play, ability_activations, appearance_count, chip_stats, board_type_counts, win_counts, turns_by_board = run_simulations(
                    num_simulations, num_racers, board_type=board_type, fixed_characters=fixed_characters, random_turn_order=True, collect_detailed_logs=True, allowed_characters=allowed, prometheus_threshold=prometheus_threshold, prometheus_starting_points=prometheus_starting_points, prometheus_check_timing=prometheus_check_timing, highroller_threshold=highroller_threshold, random_starting_bronze=random_starting_bronze
                )

                # Display results with ability data included
                self.root.after(0, lambda: self._display_race_results(
                    average_turns, average_finish_positions, all_play_by_play,
                    ability_activations, appearance_count, chip_stats,
                    win_counts, edition, num_simulations, turns_by_board
                ))
            except Exception as e:
                # Fix: Capture the exception message before using it in the lambda
                error_msg = str(e)
                self.root.after(0, lambda error_msg=error_msg: messagebox.showerror("Error", f"An error occurred: {error_msg}"))

        threading.Thread(target=run_simulations_thread).start()
    
    def _display_race_results(self, average_turns, average_finish_positions, all_play_by_play,
                          ability_activations=None, appearance_count=None, chip_stats=None,
                          win_counts=None, edition=None, num_simulations=None,
                          turns_by_board=None):
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
        self.race_results_text.insert(tk.END, f"Average number of turns per race: {average_turns:.2f}\n")
        if turns_by_board:
            mild_avg = turns_by_board.get("Mild")
            wild_avg = turns_by_board.get("Wild")
            self.race_results_text.insert(tk.END,
                f"  Mild board: {mild_avg:.2f}\n" if mild_avg is not None else "  Mild board: —\n")
            self.race_results_text.insert(tk.END,
                f"  Wild board: {wild_avg:.2f}\n" if wild_avg is not None else "  Wild board: —\n")
        self.race_results_text.insert(tk.END, "\n")
        
        # Calculate average points and ability triggers per race.
        # Sum each character's avg points × appearances to get total points awarded
        # across all races, then divide by num_simulations for per-race average.
        # This correctly captures gold/silver from finishing positions plus bronze
        # from both character abilities (Hare, LovableLoser) and Wild board spaces.
        total_ability_triggers_per_race = 0
        total_points_per_race = 0
        sims_run = self.num_simulations_var.get()
        if chip_stats and appearance_count and sims_run:
            total_points_per_race = sum(
                stats.get('points_avg', 0) * appearance_count.get(char, 0)
                for char, stats in chip_stats.items()
            ) / sims_run
        
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
        
        self.race_results_text.insert(tk.END, "For detailed character analysis, please check the 'Character Analysis' tab.\n\n")

        # Update the export button state to show logs are available
        if hasattr(self, 'export_button') and self.export_button:
            self.export_button.config(state=tk.NORMAL)

        # Push results into the Character Analysis tab
        ranking = self._build_ranking_from_race_results(
            average_finish_positions, ability_activations, appearance_count, win_counts, chip_stats
        )
        sims_label = num_simulations if num_simulations is not None else self.num_simulations_var.get()
        ed_label = edition or "?"
        status = (f"Showing {sims_label} single-race simulations "
                  f"({ed_label} edition). Click headers to sort.")
        self._populate_analysis_table(ranking, status)

    def _build_ranking_from_race_results(self, average_finish_positions, ability_activations,
                                         appearance_count, win_counts, chip_stats):
        """Convert run_simulations outputs into a ranking list for the analysis table."""
        ranking = []
        for char, appearances in (appearance_count or {}).items():
            if appearances <= 0:
                continue
            avg_pos = average_finish_positions.get(char)
            if avg_pos is None:
                continue
            wins = (win_counts or {}).get(char, 0)
            win_rate = (wins / appearances) * 100 if appearances else 0.0
            avg_abil = (ability_activations or {}).get(char, 0)
            char_chips = (chip_stats or {}).get(char) or {}
            avg_pts = char_chips.get("points_avg", 0)
            ranking.append({
                "character": char,
                "appearances": appearances,
                "win_rate": win_rate,
                "avg_position": avg_pos,
                "avg_points": avg_pts,
                "avg_ability_triggers": avg_abil,
            })
        ranking.sort(key=lambda x: (-x["win_rate"], x["avg_position"]))
        return ranking
    
    def _setup_character_analysis_tab(self):
        # Status bar at the top
        self.analysis_status_var = tk.StringVar(
            value="Run a simulation on the Single Race or Tournament tab to populate this view."
        )
        ttk.Label(
            self.character_analysis_tab,
            textvariable=self.analysis_status_var,
            anchor="w",
        ).pack(fill="x", padx=10, pady=(10, 0))

        # Rankings table
        table_frame = ttk.LabelFrame(self.character_analysis_tab, text="Character Rankings")
        table_frame.pack(fill="both", expand=True, padx=10, pady=10)

        columns = ("character", "appearances", "win_rate", "avg_position", "avg_points", "avg_abilities")
        self.analysis_tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=24)
        self.analysis_tree.heading("character", text="Character", command=lambda: self._sort_analysis_tree("character", numeric=False))
        self.analysis_tree.heading("appearances", text="Races", command=lambda: self._sort_analysis_tree("appearances", numeric=True, reverse=True))
        self.analysis_tree.heading("win_rate", text="Win %", command=lambda: self._sort_analysis_tree("win_rate", numeric=True, reverse=True))
        self.analysis_tree.heading("avg_position", text="Avg Pos", command=lambda: self._sort_analysis_tree("avg_position", numeric=True, reverse=False))
        self.analysis_tree.heading("avg_points", text="Avg Points", command=lambda: self._sort_analysis_tree("avg_points", numeric=True, reverse=True))
        self.analysis_tree.heading("avg_abilities", text="Avg Abilities", command=lambda: self._sort_analysis_tree("avg_abilities", numeric=True, reverse=True))

        self.analysis_tree.column("character", width=140, anchor="w")
        self.analysis_tree.column("appearances", width=70, anchor="e")
        self.analysis_tree.column("win_rate", width=70, anchor="e")
        self.analysis_tree.column("avg_position", width=80, anchor="e")
        self.analysis_tree.column("avg_points", width=90, anchor="e")
        self.analysis_tree.column("avg_abilities", width=100, anchor="e")

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=self.analysis_tree.yview)
        self.analysis_tree.configure(yscrollcommand=scrollbar.set)
        self.analysis_tree.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        scrollbar.pack(side="right", fill="y")

    def _populate_analysis_table(self, ranking, status):
        """Refresh the Character Analysis tab with a ranking list and a status string."""
        for row in self.analysis_tree.get_children():
            self.analysis_tree.delete(row)
        for entry in ranking:
            avg_abil = entry.get("avg_ability_triggers")
            avg_pts = entry.get("avg_points")
            self.analysis_tree.insert("", "end", values=(
                entry["character"],
                entry["appearances"],
                f"{entry['win_rate']:.1f}",
                f"{entry['avg_position']:.2f}",
                f"{avg_pts:.2f}" if avg_pts is not None else "—",
                f"{avg_abil:.2f}" if avg_abil is not None else "—",
            ))
        self.analysis_status_var.set(status)

    def _sort_analysis_tree(self, column, numeric=False, reverse=False):
        items = [(self.analysis_tree.set(child, column), child) for child in self.analysis_tree.get_children("")]
        if numeric:
            items.sort(key=lambda x: float(x[0]) if x[0] not in ("", "—") else 0.0, reverse=reverse)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=reverse)
        for index, (_, child) in enumerate(items):
            self.analysis_tree.move(child, "", index)

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