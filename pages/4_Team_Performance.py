import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import load_all, filter_years, dark_chart, sidebar_year_filter, VALORANT_RED

st.set_page_config(page_title="Team Performance", page_icon="🏆", layout="wide")
st.title("🏆 Team Performance")

data   = load_all()
years  = sidebar_year_filter()
scores = filter_years(data["scores"],   years)
wl     = filter_years(data["win_loss"], years)
eco    = filter_years(data["eco"],      years)

tab1, tab2, tab3 = st.tabs(["📋 Match Results", "💥 Round Win Methods", "💰 Eco Efficiency"])

# ── Tab 1: Match Results ──────────────────────────────────────────────────────
with tab1:
    if scores.empty:
        st.warning("No match data for selected seasons.")
    else:
        scores["Winner"] = scores["Match Result"].str.replace(" won", "", regex=False).str.strip()

        win_counts = scores["Winner"].value_counts().reset_index()
        win_counts.columns = ["Team", "Wins"]

        # Total matches per team (appears as Team A or Team B)
        ta = scores.groupby("Team A").size().reset_index(name="P_A").rename(columns={"Team A": "Team"})
        tb = scores.groupby("Team B").size().reset_index(name="P_B").rename(columns={"Team B": "Team"})
        total = pd.merge(ta, tb, on="Team", how="outer").fillna(0)
        total["Played"] = total["P_A"] + total["P_B"]

        team_stats = pd.merge(win_counts, total[["Team", "Played"]], on="Team", how="left")
        team_stats["Win Rate %"] = (team_stats["Wins"] / team_stats["Played"] * 100).round(1)
        team_stats = team_stats.sort_values("Win Rate %", ascending=False)

        top_n = st.slider("Show top N teams", 10, 50, 20)
        display = team_stats.head(top_n)

        fig = px.bar(
            display.sort_values("Win Rate %"),
            x="Win Rate %", y="Team", orientation="h",
            color="Win Rate %", color_continuous_scale="RdYlGn",
            text="Win Rate %",
        )
        fig.add_vline(x=50, line_dash="dash", line_color="#aaa", opacity=0.5)
        dark_chart(fig, f"Top {top_n} Teams by Win Rate")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, xaxis=dict(range=[0, 105]))
        st.plotly_chart(fig, use_container_width=True)

        st.dataframe(
            display[["Team", "Wins", "Played", "Win Rate %"]].reset_index(drop=True),
            use_container_width=True, hide_index=True,
        )

# ── Tab 2: Round Win Methods ──────────────────────────────────────────────────
with tab2:
    if wl.empty:
        st.warning("No round data for selected seasons.")
    else:
        method_cols = ["Elimination", "Detonated", "Defused", "Time Expiry (No Plant)"]
        for col in method_cols:
            wl[col] = pd.to_numeric(wl[col], errors="coerce").fillna(0)

        # Overall donut
        totals = {c: wl[c].sum() for c in method_cols}
        labels = {
            "Elimination":            "Elimination",
            "Detonated":              "Spike Detonated",
            "Defused":                "Spike Defused",
            "Time Expiry (No Plant)": "Time Expiry",
        }
        fig = px.pie(
            values=list(totals.values()),
            names=[labels[c] for c in method_cols],
            hole=0.45,
            color_discrete_sequence=[VALORANT_RED, "#f39c12", "#3498db", "#2ecc71"],
        )
        dark_chart(fig, "Overall Round Win Method Distribution")
        st.plotly_chart(fig, use_container_width=True)

        # Per-team breakdown (top 15 by total rounds)
        st.subheader("Win Method Breakdown — Top Teams")
        team_wl = wl.groupby("Team")[method_cols].sum()
        team_wl["Total"] = team_wl.sum(axis=1)
        team_wl = team_wl[team_wl["Total"] > 0]
        for col in method_cols:
            team_wl[col] = (team_wl[col] / team_wl["Total"] * 100).round(1)
        team_wl = team_wl.nlargest(15, "Total").reset_index()

        melt = team_wl.melt(id_vars="Team", value_vars=method_cols, var_name="Method", value_name="%")
        melt["Method"] = melt["Method"].map(labels)

        fig2 = px.bar(
            melt, x="%", y="Team", color="Method", orientation="h", barmode="stack",
            color_discrete_sequence=[VALORANT_RED, "#f39c12", "#3498db", "#2ecc71"],
        )
        dark_chart(fig2, "Round Win Methods — Top 15 Teams (% of rounds won)")
        fig2.update_layout(xaxis_title="% of rounds won")
        st.plotly_chart(fig2, use_container_width=True)

# ── Tab 3: Eco Efficiency ─────────────────────────────────────────────────────
with tab3:
    if eco.empty:
        st.warning("No eco data for selected seasons.")
    else:
        eco["Won"]       = pd.to_numeric(eco["Won"],       errors="coerce").fillna(0)
        eco["Initiated"] = pd.to_numeric(eco["Initiated"], errors="coerce").fillna(0)

        eco_types = {
            "Pistol Won":  "Pistol",
            "Eco (won)":   "Eco",
            "$ (won)":     "Semi-Eco",
            "$$ (won)":    "Semi-Buy",
            "$$$ (won)":   "Full Buy",
            "$$$$ (won)":  "Full Buy+",
        }
        eco_f = eco[eco["Type"].isin(eco_types.keys())].copy()
        eco_f["Round Type"] = eco_f["Type"].map(eco_types)

        agg = (
            eco_f.groupby("Round Type")
            .agg(Initiated=("Initiated", "sum"), Won=("Won", "sum"))
            .reset_index()
        )
        agg["Win Rate %"] = (agg["Won"] / agg["Initiated"].replace(0, float("nan")) * 100).round(1)
        agg = agg.dropna(subset=["Win Rate %"])

        fig = px.bar(
            agg.sort_values("Win Rate %"),
            x="Round Type", y="Win Rate %",
            color="Win Rate %", color_continuous_scale="RdYlGn",
            text="Win Rate %",
        )
        fig.add_hline(y=50, line_dash="dash", line_color="#aaa", opacity=0.5,
                      annotation_text="50%", annotation_position="right")
        dark_chart(fig, "Win Rate by Economic Round Type")
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(coloraxis_showscale=False, yaxis_title="Win Rate (%)", xaxis_title="")
        st.plotly_chart(fig, use_container_width=True)

        st.caption(
            "Eco = forced buy with minimal funds · Semi = partial buy · "
            "Full Buy = complete loadout. Higher win rates show strong economic discipline."
        )

        # Round volume
        st.subheader("Volume of Rounds by Type")
        fig2 = px.bar(
            agg.sort_values("Initiated", ascending=True),
            x="Initiated", y="Round Type", orientation="h",
            color="Initiated", color_continuous_scale="Blues",
            text="Initiated",
        )
        dark_chart(fig2, "Total Rounds Initiated by Economy Type")
        fig2.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
        fig2.update_layout(coloraxis_showscale=False, xaxis_title="Rounds")
        st.plotly_chart(fig2, use_container_width=True)
