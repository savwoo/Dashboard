import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from utils import load_all, pct_to_float, filter_years, dark_chart, sidebar_year_filter, VALORANT_RED

st.set_page_config(page_title="Player Analytics", page_icon="👤", layout="wide")
st.title("👤 Player Analytics")

data  = load_all()
years = sidebar_year_filter()
df    = filter_years(data["players"], years)

# ── Clean numeric columns ─────────────────────────────────────────────────────
if not df.empty:
    df["ACS"]  = pd.to_numeric(df["Average Combat Score"],  errors="coerce")
    df["KD"]   = pd.to_numeric(df["Kills:Deaths"],          errors="coerce")
    df["ADR"]  = pd.to_numeric(df["Average Damage Per Round"], errors="coerce")
    df["HS"]   = pct_to_float(df["Headshot %"])
    df["KAST"] = pct_to_float(df.get("Kill, Assist, Trade, Survive %", pd.Series(dtype=str)))
    df["Kills"]  = pd.to_numeric(df["Kills"],  errors="coerce")
    df["Deaths"] = pd.to_numeric(df["Deaths"], errors="coerce")
    df["Rounds"] = pd.to_numeric(df["Rounds Played"], errors="coerce")

# ── Sidebar team filter ───────────────────────────────────────────────────────
if not df.empty:
    teams = ["All"] + sorted(df["Teams"].dropna().unique().tolist())
    selected_team = st.sidebar.selectbox("Team", teams)
    if selected_team != "All":
        df = df[df["Teams"] == selected_team]

# ── Aggregate per player ──────────────────────────────────────────────────────
if not df.empty:
    agg = (
        df.groupby("Player")
        .agg(
            ACS=("ACS", "mean"),
            KD=("KD", "mean"),
            ADR=("ADR", "mean"),
            HS=("HS", "mean"),
            KAST=("KAST", "mean"),
            Kills=("Kills", "sum"),
            Deaths=("Deaths", "sum"),
            Rounds=("Rounds", "sum"),
            Team=("Teams", "first"),
        )
        .reset_index()
        .dropna(subset=["ACS"])
        .round(2)
    )
else:
    agg = pd.DataFrame()

# ── Tabs ──────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🏅 Leaderboard", "📊 Scatter Analysis", "🔍 Player Spotlight"])

# ── Tab 1: Leaderboard ────────────────────────────────────────────────────────
with tab1:
    if agg.empty:
        st.warning("No data for selected filters.")
    else:
        c1, c2 = st.columns([1, 3])
        with c1:
            sort_by = st.selectbox("Sort by", ["ACS", "KD", "ADR", "HS", "KAST", "Kills"])
            top_n   = st.slider("Show top N", 10, 100, 25)

        ranked = agg.sort_values(sort_by, ascending=False).head(top_n)
        st.dataframe(
            ranked[["Player", "Team", "ACS", "KD", "ADR", "HS", "KAST", "Kills", "Rounds"]],
            use_container_width=True,
            hide_index=True,
        )

        top15 = ranked.head(15).sort_values(sort_by)
        fig = px.bar(
            top15, x=sort_by, y="Player", orientation="h",
            color=sort_by, color_continuous_scale="Reds",
        )
        dark_chart(fig, f"Top 15 Players by {sort_by}")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(fig, use_container_width=True)

# ── Tab 2: Scatter ────────────────────────────────────────────────────────────
with tab2:
    if agg.empty:
        st.warning("No data for selected filters.")
    else:
        min_rounds = st.slider("Minimum rounds played", 50, 500, 100, key="scatter_slider")
        scatter = agg[agg["Rounds"] >= min_rounds]

        fig = px.scatter(
            scatter, x="KD", y="ACS",
            hover_name="Player",
            color="Team" if "Team" in scatter.columns else None,
            size="Rounds",
            labels={"KD": "K/D Ratio", "ACS": "Avg Combat Score"},
        )
        med_acs = scatter["ACS"].median()
        fig.add_vline(x=1.0,     line_dash="dash", line_color="#aaa", opacity=0.5)
        fig.add_hline(y=med_acs, line_dash="dash", line_color="#aaa", opacity=0.5,
                      annotation_text=f"Median ACS {med_acs:.0f}", annotation_position="right")
        dark_chart(fig, "ACS vs K/D  (bubble size = rounds played)")
        st.plotly_chart(fig, use_container_width=True)

        st.caption("Players above the median line and to the right of K/D=1 are generally high-impact performers.")

# ── Tab 3: Player Spotlight ───────────────────────────────────────────────────
with tab3:
    if agg.empty:
        st.warning("No data for selected filters.")
    else:
        player_list     = sorted(agg["Player"].dropna().unique().tolist())
        selected_player = st.selectbox("Select a player", player_list)
        row = agg[agg["Player"] == selected_player].iloc[0]

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("ACS",    f"{row['ACS']:.0f}")
        m2.metric("K/D",    f"{row['KD']:.2f}")
        m3.metric("ADR",    f"{row['ADR']:.0f}")
        m4.metric("HS%",    f"{row['HS']:.1f}%"   if pd.notna(row['HS'])   else "N/A")
        m5.metric("KAST%",  f"{row['KAST']:.1f}%" if pd.notna(row['KAST']) else "N/A")

        # Radar chart normalised to [0, 100] relative to all players
        cats = ["ACS", "KD", "ADR", "HS", "KAST"]
        norm = {}
        for cat in cats:
            col_max = agg[cat].max()
            col_min = agg[cat].min()
            val     = row[cat]
            if pd.isna(val) or col_max == col_min:
                norm[cat] = 50
            else:
                norm[cat] = round((val - col_min) / (col_max - col_min) * 100, 1)

        fig = go.Figure(go.Scatterpolar(
            r=list(norm.values()),
            theta=cats,
            fill="toself",
            fillcolor=f"rgba(255,70,85,0.25)",
            line=dict(color=VALORANT_RED, width=2),
            name=selected_player,
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
            showlegend=False,
            title=f"{selected_player}  —  Performance Radar (percentile vs. all players)",
            template="plotly_dark",
            plot_bgcolor="#0e1117",
            paper_bgcolor="#0e1117",
        )
        st.plotly_chart(fig, use_container_width=True)

        # Per-year breakdown for this player
        st.subheader(f"{selected_player} — Season Breakdown")
        py = filter_years(data["players"], years)
        if not py.empty:
            py["ACS"] = pd.to_numeric(py["Average Combat Score"], errors="coerce")
            py["KD"]  = pd.to_numeric(py["Kills:Deaths"], errors="coerce")
            py_player = py[py["Player"] == selected_player]
            if not py_player.empty:
                season_agg = py_player.groupby("Year").agg(ACS=("ACS", "mean"), KD=("KD", "mean")).reset_index()
                fig2 = px.bar(
                    season_agg, x="Year", y="ACS",
                    color="ACS", color_continuous_scale="Reds",
                    text="ACS",
                )
                dark_chart(fig2, "Avg ACS by Season")
                fig2.update_traces(texttemplate="%{text:.0f}", textposition="outside")
                fig2.update_layout(coloraxis_showscale=False, yaxis_title="Avg ACS")
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.info("No per-season data found for this player in selected years.")
