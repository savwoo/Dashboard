import streamlit as st
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data"
YEARS = [2022, 2023, 2024]
VALORANT_RED = "#ff4655"

# Only load columns the dashboard actually references — cuts memory 50-70% per file
_USECOLS: dict[str, list[str]] = {
    "players_stats.csv": [
        "Tournament", "Player", "Teams", "Rounds Played",
        "Average Combat Score", "Kills:Deaths",
        "Kill, Assist, Trade, Survive %",
        "Average Damage Per Round", "Headshot %",
        "Kills", "Deaths",
    ],
    "agents_pick_rates.csv": ["Map", "Agent", "Pick Rate"],
    "maps_stats.csv": [
        "Map",
        "Attacker Side Win Percentage",
        "Defender Side Win Percentage",
    ],
    "kills_stats.csv": [
        "Map", "Player",
        "2k", "3k", "4k", "5k",
        "1v1", "1v2", "1v3", "1v4", "1v5",
        "Spike Plants", "Spike Defuses",
    ],
    "eco_stats.csv": ["Type", "Initiated", "Won"],
    "win_loss_methods_count.csv": [
        "Map", "Team",
        "Elimination", "Detonated", "Defused", "Time Expiry (No Plant)",
    ],
    "scores.csv": ["Match Name", "Team A", "Team B", "Match Result"],
    "maps_played.csv": ["Map"],
    "draft_phase.csv": ["Action", "Map"],
}

# String columns to store as category (saves ~4-8x vs object dtype)
_CATEGORIES: dict[str, list[str]] = {
    "players_stats.csv":        ["Tournament", "Player", "Teams"],
    "agents_pick_rates.csv":    ["Map", "Agent"],
    "maps_stats.csv":           ["Map"],
    "kills_stats.csv":          ["Map", "Player"],
    "eco_stats.csv":            ["Type"],
    "win_loss_methods_count.csv": ["Map", "Team"],
    "scores.csv":               ["Team A", "Team B", "Match Result"],
    "maps_played.csv":          ["Map"],
    "draft_phase.csv":          ["Action", "Map"],
}


def _downcast(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.select_dtypes("float64").columns:
        df[col] = pd.to_numeric(df[col], downcast="float")
    for col in df.select_dtypes("int64").columns:
        df[col] = pd.to_numeric(df[col], downcast="integer")
    return df


@st.cache_data(show_spinner=False)
def load_year(year: int, filename: str) -> pd.DataFrame:
    path = DATA_PATH / f"vct_{year}" / filename
    if not path.exists():
        return pd.DataFrame()
    cols = _USECOLS.get(filename)
    df = pd.read_csv(path, usecols=cols, low_memory=False)
    for col in _CATEGORIES.get(filename, []):
        if col in df.columns:
            df[col] = df[col].astype("category")
    df = _downcast(df)
    df["Year"] = year
    return df


@st.cache_data(show_spinner=False)
def load_multi_year(filename: str) -> pd.DataFrame:
    frames = [load_year(y, filename) for y in YEARS]
    frames = [f for f in frames if not f.empty]
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


@st.cache_data(show_spinner=False)
def load_all() -> dict[str, pd.DataFrame]:
    return {
        "players":  load_multi_year("players_stats.csv"),
        "agents":   load_multi_year("agents_pick_rates.csv"),
        "maps":     load_multi_year("maps_stats.csv"),
        "kills":    load_multi_year("kills_stats.csv"),
        "eco":      load_multi_year("eco_stats.csv"),
        "win_loss": load_multi_year("win_loss_methods_count.csv"),
        "scores":   load_multi_year("scores.csv"),
        "played":   load_multi_year("maps_played.csv"),
        "draft":    load_multi_year("draft_phase.csv"),
        # overview.csv removed — was loaded but never used
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
