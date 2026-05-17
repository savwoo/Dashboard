import streamlit as st
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).parent / "data"
YEARS = [2021, 2022, 2023, 2024]
VALORANT_RED = "#ff4655"


@st.cache_data
def load_year(year: int, filename: str) -> pd.DataFrame:
    path = DATA_PATH / f"vct_{year}" / filename
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path, low_memory=False)
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
