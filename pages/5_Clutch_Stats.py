import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_all, filter_years, dark_chart, sidebar_year_filter, VALORANT_RED

st.set_page_config(page_title="Clutch & Highlights", page_icon="💥", layout="wide")
st.title("💥 Clutch & Multi-Kill Stats")

data   = load_all()
years  = sidebar_year_filter()
df     = filter_years(data["kills"], years)

MULTI_KILL_COLS  = ["2k", "3k", "4k", "5k"]
CLUTCH_COLS      = ["1v1", "1v2", "1v3", "1v4", "1v5"]
BOMB_COLS        = ["Spike Plants", "Spike Defuses"]

if not df.empty:
    for col in MULTI_KILL_COLS + CLUTCH_COLS + BOMB_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    # Use All Maps rows when available, fall back to all rows
    clean = df[df["Map"] == "All Maps"].copy() if "All Maps" in df["Map"].values else df.copy()

    player_agg = clean.groupby("Player").agg(
        **{
            "2K": ("2k", "sum"),
            "3K": ("3k", "sum"),
            "4K": ("4k", "sum"),
            "5K": ("5k", "sum"),
            "1v1": ("1v1", "sum"),
            "1v2": ("1v2", "sum"),
            "1v3": ("1v3", "sum"),
            "1v4": ("1v4", "sum"),
            "1v5": ("1v5", "sum"),
            "Plants":  ("Spike Plants",  "sum"),
            "Defuses": ("Spike Defuses", "sum"),
        }
    ).reset_index()

    player_agg["Total MK"]      = player_agg[["2K", "3K", "4K", "5K"]].sum(axis=1)
    player_agg["Total Clutches"] = player_agg[["1v1", "1v2", "1v3", "1v4", "1v5"]].sum(axis=1)
else:
    player_agg = pd.DataFrame()

tab1, tab2, tab3 = st.tabs(["🔫 Multi-Kills", "🎯 Clutch Rounds", "💣 Bomb Stats"])

# ── Tab 1: Multi-Kills ────────────────────────────────────────────────────────
with tab1:
    if player_agg.empty:
        st.warning("No multi-kill data for selected seasons.")
    else:
        c1, c2 = st.columns([3, 2])

        with c1:
            top_n   = st.slider("Top N players", 5, 25, 15, key="mk_n")
            kill_t  = st.radio("Kill type", ["Total MK", "2K", "3K", "4K", "5K"], horizontal=True)
            top_mk  = player_agg.nlargest(top_n, kill_t).sort_values(kill_t)

            color_map = {
                "Total MK": "Reds", "2K": "Blues", "3K": "Oranges",
                "4K": "Purples", "5K": "Greens",
            }
            fig = px.bar(top_mk, x=kill_t, y="Player", orientation="h",
                         color=kill_t, color_continuous_scale=color_map[kill_t])
            dark_chart(fig, f"Top {top_n} Players — {kill_t}")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            mk_totals = {
                "2K": player_agg["2K"].sum(),
                "3K": player_agg["3K"].sum(),
                "4K": player_agg["4K"].sum(),
                "5K": player_agg["5K"].sum(),
            }
            fig2 = px.pie(
                values=list(mk_totals.values()),
                names=list(mk_totals.keys()),
                hole=0.45,
                color_discrete_sequence=["#3498db", "#f39c12", VALORANT_RED, "#8e44ad"],
            )
            dark_chart(fig2, "Multi-Kill Type Distribution")
            st.plotly_chart(fig2, use_container_width=True)

            total_5k = int(player_agg["5K"].sum())
            total_mk = int(player_agg["Total MK"].sum())
            st.metric("Total Ace Rounds (5K)", f"{total_5k:,}")
            st.metric("Total Multi-Kills",     f"{total_mk:,}")

# ── Tab 2: Clutch Rounds ──────────────────────────────────────────────────────
with tab2:
    if player_agg.empty:
        st.warning("No clutch data for selected seasons.")
    else:
        c1, c2 = st.columns([3, 2])

        with c1:
            top_c   = st.slider("Top N players", 5, 25, 15, key="clutch_n")
            clutch_t = st.radio("Clutch type", ["Total Clutches", "1v1", "1v2", "1v3", "1v4", "1v5"],
                                horizontal=True)
            top_cl  = player_agg.nlargest(top_c, clutch_t).sort_values(clutch_t)

            fig = px.bar(top_cl, x=clutch_t, y="Player", orientation="h",
                         color=clutch_t, color_continuous_scale="Purples")
            dark_chart(fig, f"Top {top_c} Players — {clutch_t}")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            clutch_totals = {
                "1v1": player_agg["1v1"].sum(),
                "1v2": player_agg["1v2"].sum(),
                "1v3": player_agg["1v3"].sum(),
                "1v4": player_agg["1v4"].sum(),
                "1v5": player_agg["1v5"].sum(),
            }
            fig2 = px.pie(
                values=list(clutch_totals.values()),
                names=list(clutch_totals.keys()),
                hole=0.45,
                color_discrete_sequence=["#2ecc71", "#f39c12", VALORANT_RED, "#8e44ad", "#e67e22"],
            )
            dark_chart(fig2, "Clutch Difficulty Breakdown")
            st.plotly_chart(fig2, use_container_width=True)

            rare  = int(player_agg[["1v4", "1v5"]].sum().sum())
            total = int(player_agg["Total Clutches"].sum())
            st.metric("Total Clutches",          f"{total:,}")
            st.metric("Miracle Clutches (1v4/5)", f"{rare:,}")

# ── Tab 3: Bomb Stats ─────────────────────────────────────────────────────────
with tab3:
    if player_agg.empty:
        st.warning("No bomb stat data for selected seasons.")
    else:
        c1, c2 = st.columns(2)

        with c1:
            top_plants = player_agg.nlargest(15, "Plants")[["Player", "Plants"]].sort_values("Plants")
            fig = px.bar(top_plants, x="Plants", y="Player", orientation="h",
                         color="Plants", color_continuous_scale="Oranges")
            dark_chart(fig, "Top 15 Spike Planters")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            top_def = player_agg.nlargest(15, "Defuses")[["Player", "Defuses"]].sort_values("Defuses")
            fig = px.bar(top_def, x="Defuses", y="Player", orientation="h",
                         color="Defuses", color_continuous_scale="Blues")
            dark_chart(fig, "Top 15 Spike Defusers")
            fig.update_layout(coloraxis_showscale=False)
            st.plotly_chart(fig, use_container_width=True)

        # Plants vs Defuses scatter
        st.subheader("Plants vs Defuses — Player Profile")
        pd_scatter = player_agg[(player_agg["Plants"] > 0) | (player_agg["Defuses"] > 0)]
        fig3 = px.scatter(
            pd_scatter, x="Plants", y="Defuses",
            hover_name="Player", size="Total MK",
            color="Total Clutches",
            color_continuous_scale="Reds",
            labels={"Plants": "Spike Plants", "Defuses": "Spike Defuses"},
        )
        dark_chart(fig3, "Spike Plants vs Defuses  (bubble size = multi-kills, colour = clutches)")
        st.plotly_chart(fig3, use_container_width=True)
        st.caption("Players in the top-right are all-around clutch performers on both sides.")
