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
        num_simulations = st.slider("Number of Simulations", 1, 10000, 10000)
    with col_racers:
        num_racers = st.slider("Number of Racers", 2, 10, 5)

    # The set of characters allowed for this edition
    edition_chars = list(get_characters_by_edition(edition).keys())

    # ---- Board type checkboxes -------------------------------------------
    st.write("**Board Types**")
    col_mild, col_wild, col_sportals = st.columns(3)
    with col_mild:
        use_mild = st.checkbox("Mild", value=True)
    with col_wild:
        use_wild = st.checkbox("Wild", value=True)
    with col_sportals:
        use_sportals = st.checkbox(
            "Sportals",
            value=True,
            help="Wormhole board: 7 paired portals (4-7, 8-12, 11-15, "
                 "16-18, 17-22, 20-23, 24-28). Stopping on a portal warps "
                 "you to its partner. Per warp rules, this doesn't trigger "
                 "stopping/passing abilities — but share-space effects "
                 "(Duelist, alt-Penguin) still fire at the destination.",
        )

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
    # Toggles are grouped by character/feature and laid out vertically
    # inside a fixed-height scrollable container — there are enough now
    # that a single horizontal row got cramped.
    with st.expander("Advanced settings", expanded=False):
        with st.container(height=420):
            st.markdown("**Prometheus**")
            col_prom1, col_prom2, col_prom3 = st.columns(3)
            with col_prom1:
                prometheus_threshold = st.number_input(
                    "Threshold",
                    min_value=0,
                    max_value=20,
                    value=2,
                    step=1,
                    help="If Prometheus is in the race, racers below this point "
                         "total trigger Prometheus's bronze handout.",
                )
            with col_prom2:
                prometheus_starting_points = st.number_input(
                    "Starting points",
                    min_value=0,
                    max_value=20,
                    value=1,
                    step=1,
                    help="Bronze chips Prometheus starts with.",
                )
            with col_prom3:
                prometheus_check_timing = st.selectbox(
                    "Check timing",
                    ["end", "start"],
                    index=1,
                    help="When in the turn cycle Prometheus checks point totals.",
                )

            st.divider()
            st.markdown("**HighRoller**")
            highroller_threshold = st.number_input(
                "Stop-at",
                min_value=2,
                max_value=12,
                value=8,
                step=1,
                help="HighRoller keeps re-rolling until total ≥ this. Higher = greedier — more chances to bust on a same-or-lower roll (no movement that turn).",
            )

            st.divider()
            st.markdown("**AntimagicalAthlete**")
            antimag_main_move_penalty = st.number_input(
                "Main-move penalty",
                min_value=0,
                max_value=6,
                value=1,
                step=1,
                help="Spaces subtracted from the main-move of any racer "
                     "strictly ahead of an active AntimagicalAthlete. "
                     "Default 1 is the canonical rule (racers ahead of "
                     "Antimag lose their powers AND get -1 to their main "
                     "move). Crank to 2+ for balance experiments; 0 disables "
                     "the penalty entirely (suppression only).",
            )

            st.divider()
            st.markdown("**Spoilsport**")
            spoilsport_threshold = st.number_input(
                "Cancel-at",
                min_value=1,
                max_value=20,
                value=5,
                step=1,
                help="Minimum lead (in spaces) every other non-eliminated "
                     "racer must have over Spoilsport before they cancel the "
                     "race. Raise to make Spoilsport more patient, lower to "
                     "make them quicker to rage-quit. Printed card is 3.",
            )

            st.divider()
            st.markdown("**Penguin**")
            penguin_recovery_move = st.slider(
                "Recovery move",
                min_value=0,
                max_value=12,
                value=6,
                step=1,
                help="Spaces a tripped Penguin auto-moves on their recovery "
                     "turn (instead of skipping the main move). 0 = off "
                     "(behaves like a normal racer — skips main move when "
                     "tripped). Bypasses the roll pipeline, so Gunk/Coach/etc. "
                     "don't modify it. Only applies to Penguin's default "
                     "(trip-on-pass) mode; alt mode ignores this and doubles "
                     "the roll instead.",
            )
            penguin_alt_mode = st.checkbox(
                "Alt mode (share-space + doubled-roll recovery)",
                value=True,
                help="Switches Penguin's rule set. OFF (default): trip when "
                     "passed, recover via the slider above. ON: trip when "
                     "stopping on a racer or when a racer stops on you, "
                     "recover by moving DOUBLE your roll (slider above is "
                     "ignored).",
            )

            st.divider()
            st.markdown("**Buddy**")
            buddy_warp_range = st.slider(
                "Warp range",
                min_value=0,
                max_value=15,
                value=5,
                step=1,
                help="Max distance (in spaces) between Buddy and their picked "
                     "friend that allows the pre-Main-Move warp to fire. "
                     "Default 3 matches the printed card. 0 = warp disabled "
                     "(Buddy still picks a friend at race start, just never "
                     "warps).",
            )

            st.divider()
            st.markdown("**Cheatah**")
            cheatah_alt_mode = st.checkbox(
                "Alt mode (4–6 only)",
                value=False,
                help="OFF (default): Cheatah and the guesser both pick from "
                     "1–6 (1-in-6 hit rate; wrong-guess move is 1–6). ON: "
                     "both pick from 4–6 only (1-in-3 hit rate; wrong-guess "
                     "move is 4–6 — guaranteed-bigger move when guessed "
                     "wrong, but easier to guess). Either way, this isn't "
                     "a roll, so Inchworm/Skipper/Weremouth/Gunk etc. don't "
                     "fire on it.",
            )

            st.divider()
            st.markdown("**Race-wide**")
            random_starting_bronze = st.checkbox(
                "Random starting bronze (0–4 each racer)",
                value=True,
                help="Each racer starts with 0–4 bronze chips (excluded from "
                     "the per-race points-earned average).",
            )

    # ---- Run button -------------------------------------------------------
    run_clicked = st.button("Run Simulations", type="primary")

    if run_clicked:
        # Validate inputs
        if not (use_mild or use_wild or use_sportals):
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

        # Determine board parameter for run_simulations.
        # If exactly one is selected, pass that board_type directly. If
        # multiple are selected, pass "Random" + the explicit pool so
        # Sportals only mixes in when the user opted in.
        selected_boards = []
        if use_mild:
            selected_boards.append("Mild")
        if use_wild:
            selected_boards.append("Wild")
        if use_sportals:
            selected_boards.append("Sportals")
        if len(selected_boards) == 1:
            board_type = selected_boards[0]
            random_board_pool = None
        else:
            board_type = "Random"
            random_board_pool = selected_boards

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
                penguin_recovery_move=int(penguin_recovery_move),
                buddy_warp_range=int(buddy_warp_range),
                penguin_alt_mode=penguin_alt_mode,
                random_board_pool=random_board_pool,
                cheatah_alt_mode=cheatah_alt_mode,
            )

        st.success(f"Completed {num_simulations} simulations.")

        # ---- Top-line metrics --------------------------------------------
        mild_avg = average_turns_by_board.get("Mild")
        wild_avg = average_turns_by_board.get("Wild")
        sportals_avg = average_turns_by_board.get("Sportals")
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        m1.metric("Avg turns / race", f"{average_turns:.2f}")
        m2.metric("Mild avg turns", f"{mild_avg:.2f}" if mild_avg is not None else "—")
        m3.metric("Wild avg turns", f"{wild_avg:.2f}" if wild_avg is not None else "—")
        m4.metric("Sportals avg turns", f"{sportals_avg:.2f}" if sportals_avg is not None else "—")
        m5.metric("Mild races", board_type_counts.get("Mild", 0))
        m6.metric("Wild races", board_type_counts.get("Wild", 0))
        m7.metric("Sportals races", board_type_counts.get("Sportals", 0))

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
