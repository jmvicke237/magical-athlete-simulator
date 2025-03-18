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
        export_frame = ttk.Frame(right_frame)
        export_frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(export_frame, text="Export Play-by-Play Log", 
                command=self._export_play_by_play_log).pack(side="right", padx=5)
                
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
            # Combine all logs with separators
            full_log = "\n\n" + "="*80 + "\n\n".join(self.complete_simulation_logs) + "\n\n" + "="*80 + "\n\n"
            
            # Add a header
            num_sims = len(self.complete_simulation_logs)
            header = f"COMPLETE PLAY-BY-PLAY LOGS\n{num_sims} Race Simulations\nExported on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            
            # Write content to file
            with open(file_path, 'w') as f:
                f.write(header + full_log)
            
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
        top_frame = ttk.LabelFrame(main_frame, text="Analysis Configuration")
        top_frame.pack(fill="x", padx=5, pady=5)
        
        ttk.Label(top_frame, text="Number of Simulations:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.stats_simulations_var = tk.IntVar(value=100)
        ttk.Spinbox(top_frame, from_=10, to=1000, textvariable=self.stats_simulations_var, width=5).grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        ttk.Label(top_frame, text="Racers per Race:").grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.stats_racers_var = tk.IntVar(value=4)
        ttk.Spinbox(top_frame, from_=2, to=10, textvariable=self.stats_racers_var, width=5).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Button(top_frame, text="Generate Character Statistics", command=self._generate_character_stats).grid(row=0, column=4, padx=15, pady=5)
        
        # Bottom panel - Results table
        bottom_frame = ttk.LabelFrame(main_frame, text="Character Statistics")
        bottom_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Treeview for character statistics
        self.stats_tree = ttk.Treeview(bottom_frame, 
            columns=("Rank", "Character", "Win Rate", "Avg Position", "Median Position", 
                    "Ability Triggers", "Appearances"), 
            show="headings")
        self.stats_tree.heading("Rank", text="Rank")
        self.stats_tree.heading("Character", text="Character")
        self.stats_tree.heading("Win Rate", text="Win Rate")
        self.stats_tree.heading("Avg Position", text="Avg Position")
        self.stats_tree.heading("Median Position", text="Median Position")
        self.stats_tree.heading("Ability Triggers", text="Ability Triggers")
        self.stats_tree.heading("Appearances", text="Appearances")
                
        self.stats_tree.column("Rank", width=50)
        self.stats_tree.column("Character", width=150)
        self.stats_tree.column("Win Rate", width=100)
        self.stats_tree.column("Avg Position", width=100)
        self.stats_tree.column("Median Position", width=100)
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
                
                # Show detailed error message
                self.root.after(0, lambda error_msg=error_msg, details=error_details: 
                               self._show_detailed_error(error_msg, "tournament simulation", details))
        
        threading.Thread(target=run_tournament_thread).start()
    
    def _display_tournament_results(self, results):
        self.tournament_results_text.delete(1.0, tk.END)
        
        # Display winner
        self.tournament_results_text.insert(tk.END, "Tournament Results:\n")
        self.tournament_results_text.insert(tk.END, f"Winner: {results['winner']}\n\n")
        
        # Display final standings
        self.tournament_results_text.insert(tk.END, "Final Standings:\n")
        for p in results["players"]:
            self.tournament_results_text.insert(tk.END, f"{p}\n")
        
        # Display race results
        for i, race in enumerate(results["race_results"]):
            self.tournament_results_text.insert(tk.END, f"\nRace {i+1}:\n")
            for place, player in race["placements"]:
                self.tournament_results_text.insert(tk.END, f"{place}: {player.name} ({player.piece})\n")
            
            # Display a sample of the play-by-play
            self.tournament_results_text.insert(tk.END, "\nPlay-by-Play Highlights:\n")
            play_by_play_sample = race["play_by_play"][:20]  # Show first 20 lines
            for line in play_by_play_sample:
                self.tournament_results_text.insert(tk.END, f"{line}\n")
            
            if len(race["play_by_play"]) > 20:
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
        def run_simulations_thread():
            try:
                average_turns, average_finish_positions, all_play_by_play, complete_logs = run_simulations(
                    num_simulations, num_racers, fixed_characters, random_turn_order=True
                )
                
                # Store complete logs in the instance
                self.complete_simulation_logs = complete_logs
                
                # Display results
                self.root.after(0, lambda: self._display_race_results(
                    average_turns, average_finish_positions, all_play_by_play
                ))
            except Exception as error:
                # Log the full exception
                error_details = log_exception(error, "race simulations")
                error_msg = str(error)
                
                # Show detailed error message in a scrollable dialog
                self.root.after(0, lambda error_msg=error_msg, details=error_details: 
                            self._show_detailed_error(error_msg, "race simulations", details))
        
        threading.Thread(target=run_simulations_thread).start()
    
    def _display_race_results(self, average_turns, average_finish_positions, all_play_by_play):
        self.race_results_text.delete(1.0, tk.END)
        
        # Display summary
        self.race_results_text.insert(tk.END, f"Completed {self.num_simulations_var.get()} simulations with {self.num_racers_var.get()} racers each.\n\n")
        self.race_results_text.insert(tk.END, f"Average number of turns per race: {average_turns:.2f}\n\n")
        
        # Display character performance
        self.race_results_text.insert(tk.END, "Character Performance (Average Finish Position):\n")
        
        # Sort by average position
        sorted_chars = sorted(
            [(char, pos) for char, pos in average_finish_positions.items() if pos is not None],
            key=lambda x: x[1]
        )
        
        for char, avg_pos in sorted_chars:
            self.race_results_text.insert(tk.END, f"{char}: {avg_pos:.2f}\n")
        
        # Display sample play-by-play
        self.race_results_text.insert(tk.END, "\nSample Play-by-Play (first simulation):\n")
        
        start_idx = all_play_by_play.index("--- Simulation 1 ---") + 1
        end_idx = start_idx + 50  # Show a reasonable number of lines
        
        for i in range(start_idx, min(end_idx, len(all_play_by_play))):
            self.race_results_text.insert(tk.END, f"{all_play_by_play[i]}\n")
        
        if len(all_play_by_play) > end_idx:
            self.race_results_text.insert(tk.END, "...\n")
    
    def _generate_character_stats(self):
        """Generate comprehensive character statistics."""
        # Get configuration
        num_simulations = self.stats_simulations_var.get()
        num_racers = self.stats_racers_var.get()
        
        # Clear the tree
        for item in self.stats_tree.get_children():
            self.stats_tree.delete(item)
        
        # Show a progress message in the existing tab rather than a new window
        progress_label = ttk.Label(self.character_stats_tab, 
                                text=f"Running {num_simulations} simulations...\nThis may take a few minutes.")
        progress_label.pack(pady=20)
        self.root.update()  # Force UI update to show the message
        
        def run_analysis():
            try:
                # Initialize or reset the analyzer
                if not hasattr(self, 'character_analyzer'):
                    self.character_analyzer = CharacterAnalyzer()
                
                print("Starting character analysis...")
                
                # Get desired racer counts
                racer_counts = [num_racers]
                
                # Run the analysis
                character_ranking = self.character_analyzer.analyze_all_characters(
                    num_simulations=num_simulations,
                    racer_counts=racer_counts
                )
                
                print(f"Analysis complete! Found data for {len(character_ranking)} characters")
                
                # Update UI on main thread
                self.root.after(0, lambda: self._update_stats_display(character_ranking, progress_label))
            except Exception as e:
                print(f"ERROR in character analysis: {e}")
                import traceback
                traceback.print_exc()
                self.root.after(0, lambda: self._show_detailed_error(str(e), "character statistics", 
                                                                traceback.format_exc()))
                self.root.after(0, lambda: progress_label.destroy())
        
        # Run in background thread
        threading.Thread(target=run_analysis).start()

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
                median_pos_str = f"{char_data.get('median_position', 0):.1f}"
                triggers_str = f"{char_data.get('avg_ability_triggers', 0):.1f}"
                
                # Insert into tree
                self.stats_tree.insert("", "end", values=(
                    i+1, 
                    char_data['character'], 
                    win_rate_str, 
                    avg_pos_str,
                    median_pos_str,
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
                median_pos_str = f"{char_data.get('median_position', 0):.1f}"
                triggers_str = f"{char_data.get('avg_ability_triggers', 0):.1f}"
                
                # Insert into tree
                self.stats_tree.insert("", "end", values=(
                    i+1, 
                    char_data['character'], 
                    win_rate_str, 
                    avg_pos_str,
                    median_pos_str,
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
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill="x", padx=5, pady=5)
        
        # Character selection dropdown
        ttk.Label(top_frame, text="Select Character:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.analysis_character_var = tk.StringVar()
        char_dropdown = ttk.Combobox(top_frame, textvariable=self.analysis_character_var, 
                                     values=sorted(list(character_abilities.keys())), width=20)
        char_dropdown.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        char_dropdown.current(0)  # Set default selection
        
        ttk.Label(top_frame, text="Number of Simulations:").grid(row=0, column=2, padx=15, pady=5, sticky="w")
        self.analysis_simulations_var = tk.IntVar(value=50)
        ttk.Spinbox(top_frame, from_=10, to=200, textvariable=self.analysis_simulations_var, width=5).grid(row=0, column=3, padx=5, pady=5, sticky="w")
        
        ttk.Button(top_frame, text="Analyze Character", command=self._run_character_analysis).grid(row=0, column=4, padx=15, pady=5)
        
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
        num_simulations = self.analysis_simulations_var.get()
        
        # Clear current content
        self.character_report_text.delete(1.0, tk.END)
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
        
        self.character_report_text.insert(tk.END, f"Analyzing {character}...\nRunning {num_simulations} simulations. This may take a minute...\n\n")
        self.root.update()
        
        # Run analysis in a separate thread
        def analysis_thread():
            try:
                # Generate the report
                report = self.character_analyzer.generate_character_report(character, num_simulations)
                
                # Get results for plotting
                results = self.character_analyzer.analyze_character(character, num_simulations)
                
                # Update UI on the main thread
                self.root.after(0, lambda: self._display_character_analysis(character, report, results))
            except Exception as error:
                # Log the full exception
                error_details = log_exception(error, "character analysis")
                error_msg = str(error)
                
                # Show detailed error message
                self.root.after(0, lambda error_msg=error_msg, details=error_details: 
                               self._show_detailed_error(error_msg, "character analysis", details))
        
        threading.Thread(target=analysis_thread).start()
    
    def _display_character_analysis(self, character, report, results):
        """Display the character analysis results."""
        # Update report text
        self.character_report_text.delete(1.0, tk.END)
        self.character_report_text.insert(tk.END, report)
        
        # Create position distribution plot
        try:
            fig1 = self.character_analyzer.plot_position_distribution(character, results)
            
            # Create canvas for the figure
            canvas1 = FigureCanvasTkAgg(fig1, master=self.plot_frame)
            canvas1.draw()
            canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
            # Create a second plot showing movement statistics
            move_stats = results["move_statistics"]
            labels = ["Average", "Maximum", "Minimum"]
            values = [move_stats["average_move"], move_stats["max_move"], move_stats["min_move"]]
            
            fig2 = plt.figure(figsize=(8, 4))
            plt.bar(labels, values, color=["blue", "green", "orange"])
            plt.title(f"Movement Statistics for {character}")
            plt.ylabel("Spaces Moved")
            
            for i, v in enumerate(values):
                plt.text(i, v, f"{v:.2f}", ha='center', va='bottom')
            
            canvas2 = FigureCanvasTkAgg(fig2, master=self.plot_frame)
            canvas2.draw()
            canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
            
        except Exception as e:
            print(f"Error creating plots: {e}")


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