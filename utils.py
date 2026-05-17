import streamlit as st
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data"
YEARS = [2022, 2023, 2024]   # 2021 excluded — too large for Streamlit Cloud free tier
VALORANT_RED = "#ff4655"

# String columns converted to category dtype to cut memory ~4-8x
_CATEGORY_COLS = {
    "players_stats.csv":        ["Tournament", "Stage", "Match Type", "Player", "Teams", "Agents"],
    "agents_pick_rates.csv":    ["Tournament", "Stage", "Match Type", "Map", "Agent"],
    "maps_stats.csv":           ["Tournament", "Stage", "Match Type", "Map"],
    "kills_stats.csv":          ["Tournament", "Stage", "Match Type", "Match Name", "Map", "Team", "Player", "Agents"],
    "eco_stats.csv":            ["Tournament", "Stage", "Match Type", "Match Name", "Map", "Team", "Type"],
    "win_loss_methods_count.csv": ["Tournament", "Stage", "Match Type", "Match Name", "Map", "Team"],
    "scores.csv":               ["Tournament", "Stage", "Match Type", "Match Name", "Team A", "Team B", "Match Result"],
    "maps_played.csv":          ["Tournament", "Stage", "Match Type", "Match Name", "Map"],
    "draft_phase.csv":          ["Tournament", "Stage", "Match Type", "Match Name", "Team", "Action", "Map"],
    "overview.csv":             ["Tournament", "Stage", "Match Type", "Match Name", "Map", "Player", "Team", "Agents", "Side"],
}


@st.cache_data
def load_year(year: int, filename: str) -> pd.DataFrame:
    path = DATA_PATH / f"vct_{year}" / filename
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
    # Downcast string columns to category to save memory
    for col in _CATEGORY_COLS.get(filename, []):
        if col in df.columns:
            df[col] = df[col].astype("category")
    df["Year"] = year
    return df


@st.cache_data
def load_multi_year(filename: str) -> pd.DataFrame:
    frames = [load_year(y, filename) for y in YEARS]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@st.cache_data
def load_all() -> dict[str, pd.DataFrame]:
    return {
        "players":   load_multi_year("players_stats.csv"),
        "agents":    load_multi_year("agents_pick_rates.csv"),
        "maps":      load_multi_year("maps_stats.csv"),
        "overview":  load_multi_year("overview.csv"),
        "kills":     load_multi_year("kills_stats.csv"),
        "eco":       load_multi_year("eco_stats.csv"),
        "win_loss":  load_multi_year("win_loss_methods_count.csv"),
        "scores":    load_multi_year("scores.csv"),
        "played":    load_multi_year("maps_played.csv"),
        "draft":     load_multi_year("draft_phase.csv"),
    }


def pct_to_float(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str).str.rstrip("%").str.strip(), errors="coerce"
    )


def filter_years(df: pd.DataFrame, years: list[int]) -> pd.DataFrame:
    if df.empty or not years or "Year" not in df.columns:
        return df
    return df[df["Year"].isin(years)].copy()


def dark_chart(fig, title: str = "") -> None:
    fig.update_layout(
        title=title,
        template="plotly_dark",
        plot_bgcolor="#0e1117",
        paper_bgcolor="#0e1117",
        font_color="#fafafa",
        margin=dict(t=50, b=30, l=10, r=10),
    )


def sidebar_year_filter() -> list[int]:
    return st.sidebar.multiselect(
        "Season", YEARS, default=YEARS, key="year_filter"
    )
