# Magical Athlete Simulator

A simulation tool for the "Magical Athlete" board game, designed to help analyze character abilities, game mechanics, and overall game balance.

## Overview

This project implements a complete simulation of the "Magical Athlete" board game, including:

- Individual character abilities and mechanics
- Single race simulations
- Complete 4-race tournaments with point tracking
- Character performance analysis and visualization
- Statistical comparison of different characters

The simulator provides insights into game balance, character effectiveness, and strategic considerations that can help with understanding and improving the board game design.

## Features

- **Tournament Simulation**: Simulates a complete 4-race tournament with multiple players, character drafting, and point tracking
- **Single Race Simulation**: Allows for quick simulations of individual races with configurable characters
- **Character Statistics**: Provides aggregate statistics on character performance across many simulations
- **Character Analysis**: Deep-dive analysis of individual character abilities, movement patterns, and winning strategies
- **Visualizations**: Graphical representations of character performance and race outcomes

## Installation

### Prerequisites

- Python 3.7 or higher
- tkinter (usually included with Python)
- matplotlib
- numpy

### Setup

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/magical-athlete-simulator.git
   cd magical-athlete-simulator
   ```

2. Install required dependencies:
   ```
   pip install matplotlib numpy
   ```

3. Run the application:
   ```
   python main.py
   ```

## Usage

### Tournament Simulation

1. Select the "Tournament Simulation" tab
2. Set the number of players (2-6)
3. Enter player names
4. Click "Run Tournament"
5. Review the tournament results, including race outcomes, points earned, and the overall winner

### Single Race Simulation

1. Select the "Single Race Simulation" tab
2. Configure the number of simulations and racers
3. Choose between random or fixed character selection
4. If fixed, select the characters to include
5. Click "Run Race Simulations"
6. Review the race statistics and sample play-by-play
7. Download the complete play-by-play

### Character Statistics

1. Select the "Character Statistics" tab
2. Set the number of simulations and racers per race
3. Click "Generate Character Statistics"
4. Review the ranking table of character performance

### Character Analysis - UNDER CONSTRUCTION

1. Select the "Character Analysis" tab
2. Choose a character to analyze
3. Set the number of simulations
4. Click "Analyze Character"
5. Review the detailed character report and visualizations

## Project Structure

- `main.py`: Entry point for the application
- `frontend.py`: User interface implementation
- `tournament.py`: Tournament simulation logic
- `game_simulation.py`: Single race simulation logic
- `character_analysis.py`: Character performance analysis tools
- `characters/`: Individual character class implementations
  - `base_character.py`: Base class for all characters
  - `[character_name].py`: Specific character implementations
- `config.py`: Configuration and character registry
- `board.py`: Game board implementation

## Extending the Simulator

### Adding New Characters

1. Create a new character class file in the `characters/` directory
2. Inherit from the `Character` base class
3. Implement the required methods to define the character's abilities
4. Register the character in `config.py`

### Modifying Game Rules

Game rules can be adjusted in:
- `board.py` for board-related rules
- `game_simulation.py` for race mechanics
- `tournament.py` for tournament structure and scoring

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Based on the board game "Magical Athlete" by Naotaka Shimamoto
- Thanks to all contributors and playtesters