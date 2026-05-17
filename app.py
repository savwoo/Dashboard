import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import load_all, pct_to_float, filter_years, dark_chart, sidebar_year_filter, VALORANT_RED

st.set_page_config(
    page_title="VCT Analytics Dashboard",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    [data-testid="stMetricValue"] { font-size: 2rem; color: #ff4655; }
    [data-testid="stMetricLabel"] { font-size: 0.85rem; color: #aaa; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
st.sidebar.markdown("## 🎯 VCT Dashboard")
st.sidebar.markdown("Valorant Champions Tour · 2021–2024")
st.sidebar.markdown("---")
years = sidebar_year_filter()

data = load_all()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🎯 Valorant Champions Tour Analytics")
st.caption("Professional esports data · 2021–2024 · All VCT regions")
st.markdown("---")

# ── KPI Row ───────────────────────────────────────────────────────────────────
players_df = filter_years(data["players"], years)
scores_df  = filter_years(data["scores"],  years)
played_df  = filter_years(data["played"],  years)
kills_df   = filter_years(data["kills"],   years)

col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Tournaments",   players_df["Tournament"].nunique() if not players_df.empty else 0)
col2.metric("Matches",       scores_df["Match Name"].nunique()  if not scores_df.empty  else 0)
col3.metric("Pro Players",   players_df["Player"].nunique()     if not players_df.empty else 0)
col4.metric("Maps Played",   len(played_df[played_df["Map"] != "All Maps"]) if not played_df.empty else 0)
col5.metric(
    "Ace Rounds (5K)",
    int(pd.to_numeric(kills_df["5k"], errors="coerce").fillna(0).sum()) if not kills_df.empty else 0,
)

st.markdown("---")

# ── Row 1: Agent Trends  |  Map Balance ───────────────────────────────────────
col_left, col_right = st.columns(2)

with col_left:
    st.subheader("Agent Pick Rate Trends")
    agents_df = filter_years(data["agents"], years)
    if not agents_df.empty:
        am = agents_df[agents_df["Map"] == "All Maps"].copy()
        am["Pick Rate"] = pct_to_float(am["Pick Rate"])
        top8 = am.groupby("Agent")["Pick Rate"].mean().nlargest(8).index
        trend = (
            am[am["Agent"].isin(top8)]
            .groupby(["Year", "Agent"])["Pick Rate"]
            .mean()
            .reset_index()
        )
        fig = px.line(
            trend, x="Year", y="Pick Rate", color="Agent", markers=True,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        dark_chart(fig)
        fig.update_layout(
            yaxis_title="Avg Pick Rate (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

with col_right:
    st.subheader("Map Balance: Attacker vs Defender")
    maps_df = filter_years(data["maps"], years)
    if not maps_df.empty:
        mb = maps_df[maps_df["Map"] != "All Maps"].copy()
        mb["Atk%"] = pct_to_float(mb["Attacker Side Win Percentage"])
        mb["Def%"] = pct_to_float(mb["Defender Side Win Percentage"])
        bal = mb.groupby("Map")[["Atk%", "Def%"]].mean().reset_index()
        bal = bal.sort_values("Atk%")

        fig = go.Figure()
        fig.add_bar(
            y=bal["Map"], x=bal["Atk%"], name="Attacker",
            orientation="h", marker_color=VALORANT_RED,
        )
        fig.add_bar(
            y=bal["Map"], x=bal["Def%"], name="Defender",
            orientation="h", marker_color="#3498db",
        )
        fig.add_vline(x=50, line_dash="dash", line_color="#aaa", opacity=0.4)
        dark_chart(fig)
        fig.update_layout(
            barmode="overlay",
            xaxis_title="Win %",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, use_container_width=True)

# ── Row 2: Top Players  |  Round Win Methods ──────────────────────────────────
col_a, col_b = st.columns(2)

with col_a:
    st.subheader("Top 15 Players by Avg Combat Score")
    if not players_df.empty:
        ps = players_df.copy()
        ps["ACS"] = pd.to_numeric(ps["Average Combat Score"], errors="coerce")
        top_acs = (
            ps.groupby("Player")["ACS"]
            .mean()
            .dropna()
            .nlargest(15)
            .reset_index()
            .sort_values("ACS")
        )
        fig = px.bar(
            top_acs, x="ACS", y="Player", orientation="h",
            color="ACS", color_continuous_scale="Reds",
        )
        dark_chart(fig)
        fig.update_layout(coloraxis_showscale=False, xaxis_title="Avg ACS")
        st.plotly_chart(fig, use_container_width=True)

with col_b:
    st.subheader("Round Win Methods — All Seasons")
    wl_df = filter_years(data["win_loss"], years)
    if not wl_df.empty:
        method_cols = {
            "Elimination":           "Elimination",
            "Detonated":             "Spike Detonated",
            "Defused":               "Spike Defused",
            "Time Expiry (No Plant)": "Time Expiry",
        }
        totals = {
            label: pd.to_numeric(wl_df[col], errors="coerce").fillna(0).sum()
            for col, label in method_cols.items()
        }
        fig = px.pie(
            values=list(totals.values()),
            names=list(totals.keys()),
            hole=0.45,
            color_discrete_sequence=[VALORANT_RED, "#f39c12", "#3498db", "#2ecc71"],
        )
        dark_chart(fig)
        st.plotly_chart(fig, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    "Data sourced from VCT official stats · Navigate using the sidebar to explore "
    "Player Analytics, Agent Meta, Map Analysis, Team Performance, and Clutch Stats."
)
