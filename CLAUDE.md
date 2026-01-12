# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build/Run Commands
- Run simulation: `python3 main.py`
- Install dependencies: `pip install -r requirements.txt`
- Character analysis: `python3 character_analysis.py`
- Game simulation: `python3 game_simulation.py`

## Code Style Guidelines
- Follow PEP 8 with 4-space indentation
- **Naming**: CamelCase for classes, snake_case for methods/variables
- **Imports**: Standard library first, third-party second, local imports last
- **Error handling**: Use try/except with specific exceptions and context logging
- **Documentation**: Docstrings for classes and important methods
- Use the `track_recursion_depth` decorator for recursive functions
- Log important events using `debug_utils.logger`
- Guard against infinite recursion with depth tracking

## Testing
No formal test suite exists. Validate functionality through game simulation runs.