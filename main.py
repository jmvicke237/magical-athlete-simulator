# main.py - Entry point for the Magical Athlete Simulator
import sys
import tkinter as tk
from frontend import MagicalAthleteApp

def main():
    """Main entry point for the application."""
    print("Starting Magical Athlete Simulator...")
    
    # Create the main application window
    root = tk.Tk()
    app = MagicalAthleteApp(root)
    
    # Configure the main window
    root.title("Magical Athlete Simulator")
    root.minsize(1000, 700)
    
    # Set a more appealing theme if available
    try:
        style = tk.ttk.Style()
        available_themes = style.theme_names()
        if 'clam' in available_themes:
            style.theme_use('clam')
        elif 'vista' in available_themes:
            style.theme_use('vista')
    except Exception as e:
        print(f"Could not set theme: {e}")
    
    # Start the application
    try:
        root.mainloop()
    except KeyboardInterrupt:
        print("Application terminated by user.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        print("Exiting Magical Athlete Simulator.")

if __name__ == "__main__":
    main()