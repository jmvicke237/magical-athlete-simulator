# Create a new file: app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from game_simulation import run_simulations
from config import character_abilities

st.title("Magical Athlete Simulator")

tab1, tab2, tab3 = st.tabs(["Race Simulation", "Character Statistics", "About"])

with tab1:
    st.header("Single Race Simulation")
    num_simulations = st.slider("Number of Simulations", 1, 500, 100)
    num_racers = st.slider("Number of Racers", 2, 10, 4)
    
    # Character selection
    character_selection = st.radio("Character Selection", ["Random", "Fixed"])
    
    if character_selection == "Fixed":
        all_characters = sorted(list(character_abilities.keys()))
        selected_chars = st.multiselect("Select Characters", all_characters)
    else:
        selected_chars = None
    
    if st.button("Run Simulations"):
        with st.spinner("Running simulations..."):
            average_turns, average_finish_positions, _, complete_logs = run_simulations(
                num_simulations, num_racers, selected_chars, random_turn_order=True
            )
            
            st.success(f"Completed {num_simulations} simulations!")
            st.write(f"Average turns per race: {average_turns:.2f}")
            
            # Show character performance
            st.subheader("Character Performance")
            
            # Convert to DataFrame for easy display
            char_data = []
            for char, avg_pos in average_finish_positions.items():
                if avg_pos is not None:
                    char_data.append({"Character": char, "Avg Position": avg_pos})
            
            df = pd.DataFrame(char_data)
            df = df.sort_values("Avg Position")
            
            st.dataframe(df)
            
            # Show sample log
            st.subheader("Sample Play-by-Play")
            if complete_logs:
                st.text_area("First Simulation", complete_logs[0], height=400)

with tab2:
    st.header("Character Statistics")
    # Similar to tab1 but focused on character stats
    
with tab3:
    st.header("About Magical Athlete Simulator")
    st.write("""
    This simulator was created to analyze the balance and gameplay of the 
    Magical Athlete board game. It allows you to run simulations of races
    with different characters and analyze their performance.
    """)