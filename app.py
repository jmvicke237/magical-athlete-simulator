# app.py — Streamlit web app for Magical Athlete Simulator
#
# Deployed via Streamlit Community Cloud (see DEPLOYMENT.md). The Tkinter
# frontend (frontend.py) has more features (Tournament tab, full play-by-play
# export); this is the cut-down web version. Tournament mode is intentionally
# omitted here — keep this app focused on running races and sharing stats.

import io
from datetime import datetime

import pandas as pd
import streamlit as st

from config import (
    BOARD_TYPES,
    DEFAULT_BOARD_TYPE,
    DEFAULT_EDITION,
    EDITIONS,
    character_abilities,
    get_characters_by_edition,
)
from game_simulation import run_simulations


# ---------------------------------------------------------------------------
# Page setup
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Magical Athlete Simulator",
    page_icon="🏁",
    layout="wide",
)
st.title("Magical Athlete Simulator")

tab_race, tab_about = st.tabs(["Race Simulation", "About"])


# ---------------------------------------------------------------------------
# Race Simulation tab
# ---------------------------------------------------------------------------
with tab_race:
    # ---- Edition + sim count + racer count -------------------------------
    col_ed, col_sims, col_racers = st.columns([1, 1, 1])
    with col_ed:
        edition = st.selectbox(
            "Edition",
            EDITIONS,
            index=EDITIONS.index(DEFAULT_EDITION) if DEFAULT_EDITION in EDITIONS else 0,
            help="V1 = original characters; V2 = expansion; All = both pools.",
        )
    with col_sims:
        num_simulations = st.slider("Number of Simulations", 1, 10000, 100)
    with col_racers:
        num_racers = st.slider("Number of Racers", 2, 10, 6)

    # The set of characters allowed for this edition
    edition_chars = list(get_characters_by_edition(edition).keys())

    # ---- Board type checkboxes -------------------------------------------
    st.write("**Board Types**")
    col_mild, col_wild = st.columns(2)
    with col_mild:
        use_mild = st.checkbox("Mild", value=True)
    with col_wild:
        use_wild = st.checkbox("Wild", value=True)

    # ---- Character selection mode ----------------------------------------
    char_mode = st.radio(
        "Character Selection",
        ["Random", "Fixed"],
        horizontal=True,
        help=(
            "Random: each race draws Number-of-Racers characters from the "
            "selected edition. Fixed: every race uses exactly the characters "
            "you pick (Number-of-Racers slider is overridden by the count "
            "of selected characters)."
        ),
    )
    if char_mode == "Fixed":
        selected_chars = st.multiselect(
            "Select Characters",
            sorted(edition_chars),
            help="Pick the exact lineup that will run in every race.",
        )
    else:
        selected_chars = None

    # ---- Advanced settings (collapsed by default) ------------------------
    with st.expander("Advanced settings", expanded=False):
        col_prom1, col_prom2, col_prom3 = st.columns(3)
        with col_prom1:
            prometheus_threshold = st.number_input(
                "Prometheus threshold",
                min_value=0,
                max_value=20,
                value=3,
                step=1,
                help="If Prometheus is in the race, racers below this point "
                     "total trigger Prometheus's bronze handout.",
            )
        with col_prom2:
            prometheus_starting_points = st.number_input(
                "Prometheus starting points",
                min_value=0,
                max_value=20,
                value=0,
                step=1,
                help="Bronze chips Prometheus starts with.",
            )
        with col_prom3:
            prometheus_check_timing = st.selectbox(
                "Prometheus check timing",
                ["end", "start"],
                index=0,
                help="When in the turn cycle Prometheus checks point totals.",
            )
        col_hr, col_rsb, col_anti, col_spoil = st.columns(4)
        with col_hr:
            highroller_threshold = st.number_input(
                "HighRoller stop-at",
                min_value=2,
                max_value=12,
                value=8,
                step=1,
                help="HighRoller keeps re-rolling until they hit this total or higher.",
            )
        with col_rsb:
            random_starting_bronze = st.checkbox(
                "Random starting bronze",
                value=False,
                help="Each racer starts with 0–4 bronze chips (excluded from "
                     "the per-race points-earned average).",
            )
        with col_anti:
            antimag_main_move_penalty = st.number_input(
                "Antimag main-move penalty",
                min_value=0,
                max_value=6,
                value=0,
                step=1,
                help="Spaces subtracted from the main-move of any racer "
                     "strictly ahead of an active AntimagicalAthlete. 0 = off "
                     "(power suppression only). 1+ stacks the penalty on top "
                     "of the existing 'no powers ahead of Antimag' rule.",
            )
        with col_spoil:
            spoilsport_threshold = st.number_input(
                "Spoilsport cancel-at",
                min_value=1,
                max_value=20,
                value=3,
                step=1,
                help="Minimum lead (in spaces) every other non-eliminated "
                     "racer must have over Spoilsport before they cancel the "
                     "race. Default 3 matches the printed card; raise to make "
                     "Spoilsport more patient, lower to make them quicker to "
                     "rage-quit.",
            )

    # ---- Run button -------------------------------------------------------
    run_clicked = st.button("Run Simulations", type="primary")

    if run_clicked:
        # Validate inputs
        if not use_mild and not use_wild:
            st.error("Please select at least one board type.")
            st.stop()

        if char_mode == "Fixed":
            if not selected_chars:
                st.error("Fixed mode is selected but no characters were chosen.")
                st.stop()
            if len(selected_chars) < 2:
                st.error("Pick at least 2 characters in Fixed mode.")
                st.stop()
            # In Fixed mode the racer count is overridden by the lineup size.
            effective_racer_count = len(selected_chars)
        else:
            effective_racer_count = num_racers
            if effective_racer_count > len(edition_chars):
                st.error(
                    f"Number of Racers ({effective_racer_count}) exceeds the "
                    f"size of the {edition} character pool ({len(edition_chars)})."
                )
                st.stop()

        # Determine board parameter for run_simulations
        if use_mild and use_wild:
            board_type = "Random"
        elif use_mild:
            board_type = "Mild"
        else:
            board_type = "Wild"

        with st.spinner(f"Running {num_simulations} simulations…"):
            (
                average_turns,
                average_finish_positions,
                _all_play_by_play,
                average_ability_activations,
                appearance_count,
                average_chip_stats,
                board_type_counts,
                win_counts,
                average_turns_by_board,
            ) = run_simulations(
                num_simulations,
                effective_racer_count,
                board_type=board_type,
                fixed_characters=selected_chars,
                random_turn_order=True,
                # Detailed logs are memory-heavy on Streamlit Cloud; skip them.
                collect_detailed_logs=False,
                allowed_characters=edition_chars,
                prometheus_threshold=int(prometheus_threshold),
                prometheus_starting_points=int(prometheus_starting_points),
                prometheus_check_timing=prometheus_check_timing,
                highroller_threshold=int(highroller_threshold),
                random_starting_bronze=random_starting_bronze,
                antimag_main_move_penalty=int(antimag_main_move_penalty),
                spoilsport_threshold=int(spoilsport_threshold),
            )

        st.success(f"Completed {num_simulations} simulations.")

        # ---- Top-line metrics --------------------------------------------
        mild_avg = average_turns_by_board.get("Mild")
        wild_avg = average_turns_by_board.get("Wild")
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Avg turns / race", f"{average_turns:.2f}")
        m2.metric("Mild avg turns", f"{mild_avg:.2f}" if mild_avg is not None else "—")
        m3.metric("Wild avg turns", f"{wild_avg:.2f}" if wild_avg is not None else "—")
        m4.metric("Mild races", board_type_counts.get("Mild", 0))
        m5.metric("Wild races", board_type_counts.get("Wild", 0))

        # ---- Character performance table ---------------------------------
        st.subheader("Character Performance")
        rows = []
        for char, appearances in appearance_count.items():
            if appearances <= 0:
                continue
            avg_pos = average_finish_positions.get(char)
            if avg_pos is None:
                continue
            wins = win_counts.get(char, 0)
            chips = average_chip_stats.get(char) or {}
            rows.append({
                "Character": char,
                "Races": appearances,
                "Wins": wins,
                "Win Rate (%)": round((wins / appearances) * 100, 2) if appearances else 0.0,
                "Avg Position": round(avg_pos, 3),
                "Avg Points": round(chips.get("points_avg", 0.0), 3),
                "Avg Gold": round(chips.get("gold_avg", 0.0), 3),
                "Avg Silver": round(chips.get("silver_avg", 0.0), 3),
                "Avg Bronze": round(chips.get("bronze_avg", 0.0), 3),
                "Avg Ability Triggers": round(average_ability_activations.get(char, 0.0), 3),
            })

        if not rows:
            st.info("No characters appeared in any race. Check your filters.")
        else:
            df = pd.DataFrame(rows).sort_values(
                ["Win Rate (%)", "Avg Position"],
                ascending=[False, True],
            )

            # Streamlit's dataframe is already sortable by clicking column
            # headers — that's the in-browser sortable view. The download
            # button below gives a CSV teammates can sort in Slack/Sheets/Excel.
            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Win Rate (%)": st.column_config.NumberColumn(format="%.2f"),
                    "Avg Position": st.column_config.NumberColumn(format="%.2f"),
                    "Avg Points": st.column_config.NumberColumn(format="%.2f"),
                    "Avg Gold": st.column_config.NumberColumn(format="%.2f"),
                    "Avg Silver": st.column_config.NumberColumn(format="%.2f"),
                    "Avg Bronze": st.column_config.NumberColumn(format="%.2f"),
                    "Avg Ability Triggers": st.column_config.NumberColumn(format="%.2f"),
                },
            )

            # CSV download — raw numeric values, ready for Slack / Sheets.
            csv_buf = io.StringIO()
            # Lead with a context comment row (most spreadsheets treat it as
            # a regular row — easy to delete if it gets in the way of sort).
            context = (
                f"# {edition} edition · {num_simulations} sims · "
                f"{effective_racer_count} racers · board={board_type} · "
                f"exported {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            csv_buf.write(context + "\n")
            df.to_csv(csv_buf, index=False)
            st.download_button(
                "Download CSV",
                data=csv_buf.getvalue(),
                file_name=f"character_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )


# ---------------------------------------------------------------------------
# About tab
# ---------------------------------------------------------------------------
with tab_about:
    st.header("About Magical Athlete Simulator")
    st.markdown(
        """
        This simulator analyzes balance and gameplay for **Magical Athlete**.
        It runs many race simulations with configurable character pools and
        reports per-character performance.

        **Editions**

        - **V1** — original characters
        - **V2** — expansion characters (29 new racers)
        - **All** — V1 + V2 combined

        **Notes for the web version**

        - Tournament mode is not available here — use the desktop app
          (`python3 main.py`) for tournament simulations.
        - Detailed play-by-play logs are disabled to keep memory usage
          reasonable on Streamlit Cloud's free tier. Use the desktop app
          for full play-by-play export.
        - Click any column header in the results table to sort in-browser,
          or use **Download CSV** to share results in Slack / Google
          Sheets / Excel.
        """
    )
