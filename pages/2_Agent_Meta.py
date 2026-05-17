import streamlit as st
import plotly.express as px
import pandas as pd
from utils import load_all, pct_to_float, filter_years, dark_chart, sidebar_year_filter

st.set_page_config(page_title="Agent Meta", page_icon="🦸", layout="wide")
st.title("🦸 Agent Meta")

data   = load_all()
years  = sidebar_year_filter()
df     = filter_years(data["agents"], years)

if not df.empty:
    df["Pick Rate"] = pct_to_float(df["Pick Rate"])

all_maps_df = df[df["Map"] == "All Maps"].copy() if not df.empty else pd.DataFrame()
year_agent  = (
    all_maps_df.groupby(["Year", "Agent"])["Pick Rate"].mean().reset_index()
    if not all_maps_df.empty else pd.DataFrame()
)

tab1, tab2, tab3 = st.tabs(["📈 Trends", "🔥 Heatmap", "🗺️ By Map"])

# ── Tab 1: Trend Lines ────────────────────────────────────────────────────────
with tab1:
    if year_agent.empty:
        st.warning("No agent data for selected seasons.")
    else:
        top_n = st.slider("Number of agents to display", 4, 20, 10, key="trend_top")
        top_agents = year_agent.groupby("Agent")["Pick Rate"].mean().nlargest(top_n).index
        trend_df = year_agent[year_agent["Agent"].isin(top_agents)]

        fig = px.line(
            trend_df, x="Year", y="Pick Rate", color="Agent", markers=True,
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        dark_chart(fig, f"Top {top_n} Agents — Pick Rate Across Seasons")
        fig.update_layout(
            yaxis_title="Avg Pick Rate (%)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Year-over-year bar comparison
        st.subheader("Side-by-Side Year Comparison")
        sel_years = st.multiselect(
            "Compare seasons", sorted(year_agent["Year"].unique()), default=sorted(year_agent["Year"].unique())[-2:],
            key="compare_years",
        )
        top_compare = year_agent.groupby("Agent")["Pick Rate"].mean().nlargest(15).index
        compare_df  = year_agent[year_agent["Year"].isin(sel_years) & year_agent["Agent"].isin(top_compare)]

        fig2 = px.bar(
            compare_df, x="Agent", y="Pick Rate", color="Year",
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        dark_chart(fig2, "Agent Pick Rate — Year Comparison")
        fig2.update_layout(yaxis_title="Avg Pick Rate (%)")
        st.plotly_chart(fig2, use_container_width=True)

# ── Tab 2: Heatmap ────────────────────────────────────────────────────────────
with tab2:
    if year_agent.empty:
        st.warning("No agent data for selected seasons.")
    else:
        top_heat = st.slider("Agents to show", 10, 30, 20, key="heat_top")
        top_a = year_agent.groupby("Agent")["Pick Rate"].mean().nlargest(top_heat).index
        pivot = (
            year_agent[year_agent["Agent"].isin(top_a)]
            .pivot_table(index="Agent", columns="Year", values="Pick Rate", aggfunc="mean")
            .fillna(0)
            .sort_values(year_agent["Year"].max(), ascending=False)
        )
        fig = px.imshow(
            pivot,
            color_continuous_scale="Reds",
            aspect="auto",
            text_auto=".1f",
        )
        dark_chart(fig, f"Top {top_heat} Agents — Pick Rate Heatmap (% per season)")
        fig.update_coloraxes(colorbar_title="Pick Rate %")
        st.plotly_chart(fig, use_container_width=True)

        # Biggest risers and fallers (needs at least 2 years of data)
        if len(years) >= 2:
            st.subheader("Biggest Meta Shifts")
            min_year = min(years)
            max_year = max(years)
            y_min = year_agent[year_agent["Year"] == min_year].set_index("Agent")["Pick Rate"]
            y_max = year_agent[year_agent["Year"] == max_year].set_index("Agent")["Pick Rate"]
            delta = (y_max - y_min).dropna().reset_index()
            delta.columns = ["Agent", "Change (pp)"]
            delta = delta.sort_values("Change (pp)")

            c1, c2 = st.columns(2)
            with c1:
                risers = delta.tail(8)
                fig_r = px.bar(risers, x="Change (pp)", y="Agent", orientation="h",
                               color="Change (pp)", color_continuous_scale="Greens")
                dark_chart(fig_r, f"Biggest Risers ({min_year} → {max_year})")
                fig_r.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_r, use_container_width=True)
            with c2:
                fallers = delta.head(8)
                fig_f = px.bar(fallers, x="Change (pp)", y="Agent", orientation="h",
                               color="Change (pp)", color_continuous_scale="Reds_r")
                dark_chart(fig_f, f"Biggest Fallers ({min_year} → {max_year})")
                fig_f.update_layout(coloraxis_showscale=False)
                st.plotly_chart(fig_f, use_container_width=True)

# ── Tab 3: By Map ─────────────────────────────────────────────────────────────
with tab3:
    if df.empty:
        st.warning("No agent data for selected seasons.")
    else:
        maps_avail = sorted(df[df["Map"] != "All Maps"]["Map"].dropna().unique())
        if maps_avail:
            sel_map = st.selectbox("Select map", maps_avail)
            map_df  = df[df["Map"] == sel_map].groupby("Agent")["Pick Rate"].mean().reset_index()
            map_df  = map_df.sort_values("Pick Rate", ascending=True)

            fig = px.bar(
                map_df, x="Pick Rate", y="Agent", orientation="h",
                color="Pick Rate", color_continuous_scale="Reds",
            )
            dark_chart(fig, f"Agent Pick Rates on {sel_map}")
            fig.update_layout(coloraxis_showscale=False, xaxis_title="Avg Pick Rate (%)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No per-map agent data available for the selected seasons.")
