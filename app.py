# Create a new file: app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from game_simulation import run_simulations
from config import character_abilities

# Cache simulation results to prevent re-running on every interaction
@st.cache_data(ttl=3600)  # Cache for 1 hour
def run_cached_simulations(num_simulations, num_racers, board_type, fixed_characters_tuple, random_turn_order):
    """Cached wrapper for run_simulations to reduce memory usage and improve performance."""
    # Convert tuple back to list (tuples are hashable for caching)
    fixed_characters = list(fixed_characters_tuple) if fixed_characters_tuple else None
    return run_simulations(
        num_simulations, num_racers,
        board_type=board_type,
        fixed_characters=fixed_characters,
        random_turn_order=random_turn_order,
        collect_detailed_logs=False  # Don't collect logs to save memory
    )

st.title("Magical Athlete Simulator")

tab1, tab2 = st.tabs(["Race Simulation", "About"])

with tab1:
    st.header("Single Race Simulation")
    num_simulations = st.slider("Number of Simulations", 1, 10000, 100)
    num_racers = st.slider("Number of Racers", 2, 10, 4)

    # Board type selection
    st.write("Board Types:")
    col1, col2 = st.columns(2)
    with col1:
        use_mild = st.checkbox("Mild", value=True)
    with col2:
        use_wild = st.checkbox("Wild", value=True)

    # Character selection
    character_selection = st.radio("Character Selection", ["Random", "Fixed"])
    
    if character_selection == "Fixed":
        all_characters = sorted(list(character_abilities.keys()))
        selected_chars = st.multiselect("Select Characters", all_characters)
    else:
        selected_chars = None
    
    if st.button("Run Simulations"):
        # Validate board selection
        if not use_mild and not use_wild:
            st.error("Please select at least one board type.")
        else:
            # Determine board type parameter
            if use_mild and use_wild:
                board_type = 'Random'
            elif use_mild:
                board_type = 'Mild'
            else:
                board_type = 'Wild'

            with st.spinner("Running simulations..."):
                # Convert selected_chars to tuple for caching (lists aren't hashable)
                fixed_chars_tuple = tuple(selected_chars) if selected_chars else None

                # Use cached version to reduce memory and prevent re-runs
                average_turns, average_finish_positions, all_play_by_play, average_ability_activations, appearance_count, average_chip_stats, board_type_counts = run_cached_simulations(
                    num_simulations, num_racers, board_type=board_type, fixed_characters_tuple=fixed_chars_tuple, random_turn_order=True
                )
            
            st.success(f"Completed {num_simulations} simulations!")
            st.write(f"Average turns per race: {average_turns:.2f}")

            # Show board type usage
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Mild Board Races", board_type_counts.get('Mild', 0))
            with col2:
                st.metric("Wild Board Races", board_type_counts.get('Wild', 0))

            # Show character performance
            st.subheader("Character Performance")

            # Convert to DataFrame for easy display
            char_data = []
            for char, avg_pos in average_finish_positions.items():
                if avg_pos is not None and appearance_count.get(char, 0) > 0:
                    char_data.append({
                        "Character": char,
                        "Avg Position": avg_pos,
                        "Avg Abilities": average_ability_activations.get(char, 0),
                        "Avg Points": average_chip_stats.get(char, {}).get('points_avg', 0),
                        "Races": appearance_count.get(char, 0)
                    })

            df = pd.DataFrame(char_data)
            df = df.sort_values("Avg Position")

            st.dataframe(df, use_container_width=True, hide_index=True)

with tab2:
    st.header("About Magical Athlete Simulator")
    st.write("""
    This simulator was created to analyze the balance and gameplay of the 
    Magical Athlete board game. It allows you to run simulations of races
    with different characters and analyze their performance.
    """)