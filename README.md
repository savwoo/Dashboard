# VCT Analytics Dashboard

An interactive analytics dashboard for **Valorant Champions Tour (VCT)** professional esports data spanning 2021–2024. Built with Python, Streamlit, and Plotly.

---

## Features

| Page | What it shows |
|---|---|
| **Home** | KPI overview, agent pick rate trends, map balance, top players by ACS |
| **Player Analytics** | Leaderboard, ACS vs K/D scatter, per-player radar chart & season breakdown |
| **Agent Meta** | Pick rate trend lines, season heatmap, biggest meta risers/fallers, per-map picks |
| **Map Analysis** | Attacker vs Defender balance, map play frequency, ban/pick rates from draft phase |
| **Team Performance** | Team win rates, round win method breakdown, eco efficiency by buy type |
| **Clutch Stats** | Multi-kill leaders (2K–5K), clutch round winners (1v1–1v5), spike plant/defuse leaders |

## Data

VCT official stats · 2021–2024 · All regions  
Aggregated CSVs covering: `players_stats`, `agents_pick_rates`, `maps_stats`, `kills_stats`, `eco_stats`, `win_loss_methods_count`, `scores`, `maps_played`, `draft_phase`

## Tech Stack

- **Python 3.11+**
- **Streamlit** — multi-page app framework
- **Plotly** — interactive charts
- **Pandas** — data wrangling

## Run Locally

```bash
# 1. Clone the repo
git clone https://github.com/savwoo/Dashboard.git
cd Dashboard

# 2. Install dependencies
pip install -r requirements.txt

# 3. Launch
streamlit run app.py
```

The app opens at `http://localhost:8501`.

## Deploy (Free)

This app runs on **Streamlit Community Cloud** — not GitHub Pages (which only serves static HTML).

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub
3. Click **New app** → select this repo → set main file to `app.py`
4. Deploy — you get a public URL to share

---

*Stack: Python · Pandas · Streamlit · Plotly*
