import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import load_all, pct_to_float, filter_years, dark_chart, sidebar_year_filter, VALORANT_RED

st.set_page_config(page_title="Map Analysis", page_icon="🗺️", layout="wide")
st.title("🗺️ Map Analysis")

data   = load_all()
years  = sidebar_year_filter()
maps   = filter_years(data["maps"],   years)
played = filter_years(data["played"], years)
draft  = filter_years(data["draft"],  years)

if not maps.empty:
    maps["Atk%"] = pct_to_float(maps["Attacker Side Win Percentage"])
    maps["Def%"] = pct_to_float(maps["Defender Side Win Percentage"])

tab1, tab2, tab3 = st.tabs(["⚖️ Balance", "📊 Play Frequency", "🚫 Draft Phase"])

# ── Tab 1: Balance ────────────────────────────────────────────────────────────
with tab1:
    if maps.empty:
        st.warning("No map stats for selected seasons.")
    else:
        bal = (
            maps[maps["Map"] != "All Maps"]
            .groupby("Map")[["Atk%", "Def%"]]
            .mean()
            .reset_index()
            .sort_values("Atk%")
        )

        # Stacked horizontal bar
        fig = go.Figure()
        fig.add_bar(y=bal["Map"], x=bal["Atk%"], name="Attacker", orientation="h",
                    marker_color=VALORANT_RED)
        fig.add_bar(y=bal["Map"], x=bal["Def%"], name="Defender",  orientation="h",
                    marker_color="#3498db")
        fig.add_vline(x=50, line_dash="dash", line_color="#aaa", opacity=0.4)
        dark_chart(fig, "Attacker vs Defender Win Rate by Map")
        fig.update_layout(
            barmode="overlay",
            xaxis_title="Win %",
            xaxis=dict(range=[30, 70]),
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Deviation from 50%
        bal["Advantage"]  = bal["Atk%"] - 50
        bal["Favors"]     = bal["Advantage"].apply(lambda x: "Attacker" if x > 0 else "Defender")
        bal["abs_adv"]    = bal["Advantage"].abs()

        fig2 = px.bar(
            bal.sort_values("Advantage"),
            x="Advantage", y="Map", orientation="h",
            color="Favors",
            color_discrete_map={"Attacker": VALORANT_RED, "Defender": "#3498db"},
            text="Advantage",
        )
        fig2.add_vline(x=0, line_dash="dash", line_color="#aaa", opacity=0.5)
        dark_chart(fig2, "Side Advantage — Deviation from 50% Balance")
        fig2.update_traces(texttemplate="%{text:.1f} pp", textposition="outside")
        st.plotly_chart(fig2, use_container_width=True)

# ── Tab 2: Play Frequency ─────────────────────────────────────────────────────
with tab2:
    if played.empty:
        st.warning("No maps played data for selected seasons.")
    else:
        map_counts = (
            played[played["Map"] != "All Maps"]["Map"]
            .value_counts()
            .reset_index()
        )
        map_counts.columns = ["Map", "Times Played"]

        fig = px.bar(
            map_counts.sort_values("Times Played"),
            x="Times Played", y="Map", orientation="h",
            color="Times Played", color_continuous_scale="Reds",
        )
        dark_chart(fig, "Total Maps Played — All Matches")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

        # Per-year breakdown
        st.subheader("Maps Played — Per Season")
        py_counts = (
            played[played["Map"] != "All Maps"]
            .groupby(["Year", "Map"])
            .size()
            .reset_index(name="Count")
        )
        fig2 = px.bar(
            py_counts, x="Map", y="Count", color="Year",
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        dark_chart(fig2, "Maps Played by Season")
        fig2.update_layout(xaxis_title="", yaxis_title="Times Played")
        st.plotly_chart(fig2, use_container_width=True)

# ── Tab 3: Draft Phase ────────────────────────────────────────────────────────
with tab3:
    if draft.empty:
        st.warning("No draft phase data for selected seasons.")
    else:
        c1, c2 = st.columns(2)

        bans = (
            draft[draft["Action"] == "ban"]["Map"]
            .value_counts()
            .reset_index()
        )
        bans.columns = ["Map", "Bans"]

        picks = (
            draft[draft["Action"] == "pick"]["Map"]
            .value_counts()
            .reset_index()
        )
        picks.columns = ["Map", "Picks"]

        with c1:
            fig = px.bar(
                bans.sort_values("Bans"),
                x="Bans", y="Map", orientation="h",
                color="Bans", color_continuous_scale="Oranges",
            )
            dark_chart(fig, "Most Banned Maps")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            fig = px.bar(
                picks.sort_values("Picks"),
                x="Picks", y="Map", orientation="h",
                color="Picks", color_continuous_scale="Greens",
            )
            dark_chart(fig, "Most Picked Maps")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        # Ban/Pick ratio
        st.subheader("Ban-to-Pick Ratio")
        bp = pd.merge(bans, picks, on="Map", how="outer").fillna(0)
        bp["Ban/Pick Ratio"] = (bp["Bans"] / bp["Picks"].replace(0, float("nan"))).round(2)
        bp = bp.dropna(subset=["Ban/Pick Ratio"]).sort_values("Ban/Pick Ratio", ascending=False)
        st.dataframe(bp, use_container_width=True, hide_index=True)
        st.caption("A high Ban/Pick ratio means teams prefer to eliminate the map rather than play it.")
