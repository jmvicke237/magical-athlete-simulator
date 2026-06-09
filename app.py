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
    col_mild, col_wild, col_sportals, col_twists = st.columns(4)
    with col_mild:
        use_mild = st.checkbox("Mild", value=True)
    with col_wild:
        use_wild = st.checkbox("Wild", value=True)
    with col_sportals:
        use_sportals = st.checkbox(
            "Sportals",
            value=True,
            help="Wormhole board: 6 paired portals (4-6, 8-12, 11-15, "
                 "16-22, 20-23, 24-28). Stopping on a portal warps "
                 "you to its partner. Per warp rules, this doesn't trigger "
                 "stopping/passing abilities — but share-space effects "
                 "(Duelist) still fire at the destination.",
        )
    with col_twists:
        use_twists = st.checkbox(
            "Twists",
            value=True,
            help="Mild layout, but the first racer to pass space 13 "
                 "triggers a random Twist that applies for the rest of "
                 "the race (11 possible twists, ranging from Conveyor "
                 "Belt +3 to Mirror World position-flip to a ghost "
                 "W.E.R.E.M.O.U.T.H. that eliminates passed racers).",
        )

    # Twist selector — pin a specific twist for every Twists race, or
    # leave on "All" to draw randomly from the pool. Only meaningful when
    # the Twists board type is selected (otherwise ignored).
    if use_twists:
        from twists import get_twist_pool
        forced_twist_choice = st.selectbox(
            "Twist (when Twists board is used)",
            ["All"] + get_twist_pool(),
            index=0,
            help="\"All\" draws a random twist per race (default). Pick a "
                 "specific twist to force it on every race that uses the "
                 "Twists board — useful for isolating a single twist's "
                 "effect on character win rates.",
        )
    else:
        forced_twist_choice = "All"

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
            st.markdown("**SpeedDemon**")
            col_prom1, col_prom2, col_prom3 = st.columns(3)
            with col_prom1:
                speeddemon_threshold = st.number_input(
                    "Lead threshold",
                    min_value=0,
                    max_value=20,
                    value=4,
                    step=1,
                    help="Lead size (in spaces over the next racer) at which "
                         "SpeedDemon is eliminated. Spec: 4. Raise to let "
                         "SpeedDemon survive bigger leads before being struck "
                         "down; 0 disables the safety entirely.",
                )
            with col_prom2:
                speeddemon_starting_points = st.number_input(
                    "Starting points",
                    min_value=0,
                    max_value=20,
                    value=3,
                    step=1,
                    help="Bronze chips SpeedDemon starts the race with. "
                         "Default 3 simulates a later race in a real cup, "
                         "where SpeedDemon would already have points and the "
                         "+1/point bonus is meaningful. Set to 0 for an "
                         "isolated first-race comparison.",
                )
            with col_prom3:
                speeddemon_check_timing = st.selectbox(
                    "Check timing",
                    ["start", "end"],
                    index=0,
                    help="When the lead-too-big elimination check fires. Spec: "
                         "start (matches 'at the start of my turn'). 'end' = "
                         "check after the move instead — useful for A/B testing.",
                )

            st.divider()
            st.markdown("**ShowOff**")
            showoff_threshold = st.number_input(
                "Stop-at",
                min_value=2,
                max_value=12,
                value=5,
                step=1,
                help="ShowOff keeps re-rolling until total ≥ this. Higher = greedier — more chances to bust on a same-or-lower roll (no movement that turn).",
            )

            st.divider()
            st.markdown("**Null**")
            null_main_move_penalty = st.number_input(
                "Main-move penalty",
                min_value=0,
                max_value=6,
                value=1,
                step=1,
                help="Spaces subtracted from the main-move of any racer "
                     "strictly ahead of an active Null. "
                     "Default 1 is the canonical rule (racers ahead of "
                     "Null lose their powers AND get -1 to their main "
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
            st.markdown("**Nemesis**")
            nemesis_warp_range = st.slider(
                "Warp range",
                min_value=0,
                max_value=15,
                value=5,
                step=1,
                help="Max distance (in spaces) between Nemesis and their picked "
                     "target that allows the pre-Main-Move warp to fire. "
                     "Spec: 5. 0 = warp disabled (Nemesis still picks a target "
                     "at race start, just never warps).",
            )

            st.divider()
            st.markdown("**Cheatah**")
            cheatah_alt_mode = st.checkbox(
                "Alt mode (4–6 only)",
                value=True,
                help="OFF (default): Cheatah and the guesser both pick from "
                     "1–6 (1-in-6 hit rate; wrong-guess move is 1–6). ON: "
                     "both pick from 4–6 only (1-in-3 hit rate; wrong-guess "
                     "move is 4–6 — guaranteed-bigger move when guessed "
                     "wrong, but easier to guess). Either way, this isn't "
                     "a roll, so Inchworm/Skipper/NormalHarry/Gunk etc. don't "
                     "fire on it.",
            )

            st.divider()
            st.markdown("**Race-wide**")
            random_starting_bronze = st.checkbox(
                "Random starting bronze (0–4 each racer)",
                value=True,
                help="Each racer starts with 0–4 bronze chips (excluded from "
                     "the per-race points-earned average). Default ON simulates "
                     "a later race in a real cup, where racers already have "
                     "varying chip totals from prior races. Turn OFF for an "
                     "isolated first-race comparison.",
            )

    # ---- Run button -------------------------------------------------------
    run_clicked = st.button("Run Simulations", type="primary")

    if run_clicked:
        # Validate inputs
        if not (use_mild or use_wild or use_sportals or use_twists):
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
        if use_twists:
            selected_boards.append("Twists")
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
                average_bronze_earned,
                max_bronze_earned,
                watchdog_tally,
            ) = run_simulations(
                num_simulations,
                effective_racer_count,
                board_type=board_type,
                fixed_characters=selected_chars,
                random_turn_order=True,
                # Detailed logs are memory-heavy on Streamlit Cloud; skip them.
                collect_detailed_logs=False,
                allowed_characters=edition_chars,
                speeddemon_threshold=int(speeddemon_threshold),
                speeddemon_starting_points=int(speeddemon_starting_points),
                speeddemon_check_timing=speeddemon_check_timing,
                showoff_threshold=int(showoff_threshold),
                random_starting_bronze=random_starting_bronze,
                null_main_move_penalty=int(null_main_move_penalty),
                spoilsport_threshold=int(spoilsport_threshold),
                nemesis_warp_range=int(nemesis_warp_range),
                random_board_pool=random_board_pool,
                cheatah_alt_mode=cheatah_alt_mode,
                forced_twist=forced_twist_choice,
            )

        st.success(f"Completed {num_simulations} simulations.")

        # ---- Top-line metrics --------------------------------------------
        mild_avg = average_turns_by_board.get("Mild")
        wild_avg = average_turns_by_board.get("Wild")
        sportals_avg = average_turns_by_board.get("Sportals")
        twists_avg = average_turns_by_board.get("Twists")
        m1, m2, m3, m4, m5, m6, m7, m8, m9 = st.columns(9)
        m1.metric("Avg turns / race", f"{average_turns:.2f}")
        m2.metric("Mild avg turns", f"{mild_avg:.2f}" if mild_avg is not None else "—")
        m3.metric("Wild avg turns", f"{wild_avg:.2f}" if wild_avg is not None else "—")
        m4.metric("Sportals avg turns", f"{sportals_avg:.2f}" if sportals_avg is not None else "—")
        m5.metric("Twists avg turns", f"{twists_avg:.2f}" if twists_avg is not None else "—")
        m6.metric("Mild races", board_type_counts.get("Mild", 0))
        m7.metric("Wild races", board_type_counts.get("Wild", 0))
        m8.metric("Sportals races", board_type_counts.get("Sportals", 0))
        m9.metric("Twists races", board_type_counts.get("Twists", 0))

        # Race-economy stat: avg & max bronze chips entering the chip economy
        # per race (ability awards + board-space chips; excludes starting chips,
        # transfers between racers net to zero — see
        # Game.bronze_chips_earned_this_race).
        bz1, bz2 = st.columns(2)
        bz1.metric(
            "# of bronze chips used (avg/race)",
            f"{average_bronze_earned:.2f}",
            help="Average bronze chips earned by all racers combined per race. "
                 "Excludes chips seeded at race start (random starting bronze, "
                 "SpeedDemon's starting points). Hotel-style chip transfers between "
                 "racers net to zero. Counts things like Streaker's pass-bonus, "
                 "Hare's alone-in-lead chip, board-space bronze chips, and Pinata "
                 "twist chips.",
        )
        bz2.metric(
            "# of bronze chips used (max in a race)",
            f"{max_bronze_earned}",
            help="The most bronze chips earned by all racers combined in any "
                 "single race of this batch. Same inclusion/exclusion rules as "
                 "the average to the left.",
        )

        # ---- Watchdog / safety-net events --------------------------------
        wd = watchdog_tally
        if wd['races_with_turn_abort'] or wd['races_abilities_off'] or wd['races_max_turns_hit']:
            with st.expander(
                f"⚠️ Watchdog events fired in this batch "
                f"({wd['races_abilities_off']} abilities-off, "
                f"{wd['races_with_turn_abort']} turn-abort, "
                f"{wd['races_max_turns_hit']} max-turns)",
                expanded=False,
            ):
                w1, w2, w3 = st.columns(3)
                w1.metric(
                    "Races: abilities-off endgame",
                    wd['races_abilities_off'],
                    help="Races that ran long enough to hit ABILITIES_OFF_TURN — "
                         "all powers were switched off so plain d6 rolls could "
                         "finish the race. Search the play-by-play for "
                         "'[WATCHDOG] abilities-off'.",
                )
                w2.metric(
                    "Races: turn aborted",
                    wd['races_with_turn_abort'],
                    help=f"Races where at least one turn hit the per-turn event "
                         f"cap and was aborted ({wd['turn_abort_events']} aborted "
                         f"turns total). Search for '[WATCHDOG] turn-abort'.",
                )
                w3.metric(
                    "Races: hit hard turn cap",
                    wd['races_max_turns_hit'],
                    help="Races that reached the MAX_TURNS hard cap without "
                         "finishing (resolved by board position). Should be ~0. "
                         "Search for '[WATCHDOG] max-turns'.",
                )
        else:
            st.caption("✅ No watchdog events fired — every race finished normally.")

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
