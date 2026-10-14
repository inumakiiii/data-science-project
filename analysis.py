"""Reproduce the child-mortality analysis and both portfolio figures."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parent
DATA_FILE = ROOT / "data" / "worldbank_child_mortality.json"
OUTPUT_DIR = ROOT / "visualizations"

REGIONS = {
    "SSF": "Sub-Saharan Africa",
    "SAS": "South Asia",
    "MEA": "Middle East, North Africa, Afghanistan & Pakistan",
    "LCN": "Latin America & Caribbean",
    "EAS": "East Asia & Pacific",
    "ECS": "Europe & Central Asia",
    "NAC": "North America",
}


def load_data() -> pd.DataFrame:
    """Load the saved World Bank API response into a tidy data frame."""
    payload = json.loads(DATA_FILE.read_text(encoding="utf-8"))
    rows = payload[1]
    frame = pd.DataFrame(
        {
            "code": row["countryiso3code"],
            "year": pd.to_numeric(row["date"], errors="coerce"),
            "mortality_rate": row["value"],
        }
        for row in rows
        if row["countryiso3code"] in REGIONS
    )
    frame["region"] = frame["code"].map(REGIONS)
    return frame.dropna(subset=["year", "mortality_rate"]).sort_values(["code", "year"])


def comparison_table(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the 1990/2024 regional comparison used in the first figure."""
    selected = frame[frame["year"].isin([1990, 2024])]
    table = selected.pivot(index=["code", "region"], columns="year", values="mortality_rate")
    table = table.rename(columns={1990: "rate_1990", 2024: "rate_2024"}).reset_index()
    table["decline_pct"] = (1 - table["rate_2024"] / table["rate_1990"]) * 100
    return table.sort_values("rate_2024")


def save_comparison(table: pd.DataFrame) -> None:
    """Create a dumbbell chart comparing 1990 with 2024."""
    fig, ax = plt.subplots(figsize=(12, 7.2))
    y = range(len(table))
    ax.hlines(y, table["rate_2024"], table["rate_1990"], color="#cbd5df", linewidth=5)
    ax.scatter(table["rate_1990"], y, s=95, facecolor="white", edgecolor="#6b7280", linewidth=2, label="1990")
    colors = ["#d14f31" if code == "SSF" else "#087f8c" for code in table["code"]]
    ax.scatter(table["rate_2024"], y, s=115, color=colors, edgecolor="white", linewidth=1.5, label="2024")

    for position, row in enumerate(table.itertuples()):
        ax.text(row.rate_2024 - 3, position, f"{row.rate_2024:.1f}", ha="right", va="center", fontsize=9, color=colors[position], weight="bold")
        ax.text(row.rate_1990 + 3, position, f"{row.rate_1990:.1f}", ha="left", va="center", fontsize=9, color="#6b7280")

    ax.set_yticks(list(y), table["region"])
    ax.set_xlim(0, 210)
    ax.set_xlabel("Deaths before age five per 1,000 live births")
    ax.set_title("Child mortality fell in every region, but the gap remains", loc="left", y=1.09, fontsize=18, weight="bold")
    ax.text(0, 1.035, "Under-five mortality rate by World Bank region, 1990 vs 2024", transform=ax.transAxes, fontsize=11, color="#52606d")
    ax.grid(axis="x", color="#e5e7eb")
    ax.tick_params(axis="y", length=0, pad=10)
    ax.legend(frameon=False, ncol=2, loc="lower right")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(0.01, 0.01, "Source: World Bank, World Development Indicators (SH.DYN.MORT).", fontsize=8, color="#6b7280")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUTPUT_DIR / "regional-comparison.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def save_trends(frame: pd.DataFrame) -> None:
    """Create a line chart showing the full 1990-2024 regional trends."""
    fig, ax = plt.subplots(figsize=(12, 7.2))
    palette = {
        "SSF": "#d14f31",
        "SAS": "#7656a6",
        "MEA": "#c88a12",
        "LCN": "#087f8c",
        "EAS": "#3678bf",
        "ECS": "#4e8f52",
        "NAC": "#4b5563",
    }
    for code, region in REGIONS.items():
        series = frame[(frame["code"] == code) & frame["year"].between(1990, 2024)]
        ax.plot(series["year"], series["mortality_rate"], color=palette[code], linewidth=2.6 if code == "SSF" else 2, label=region)

    ax.set_xlim(1990, 2024)
    ax.set_ylim(0, 190)
    ax.set_xlabel("Year")
    ax.set_ylabel("Deaths before age five per 1,000 live births")
    ax.set_title("Regional progress has been broad but uneven", loc="left", y=1.09, fontsize=18, weight="bold")
    ax.text(0, 1.035, "Under-five mortality rate, 1990-2024", transform=ax.transAxes, fontsize=11, color="#52606d")
    ax.grid(color="#e5e7eb")
    ax.legend(frameon=False, fontsize=8.5, ncol=2, loc="upper right")
    for spine in ax.spines.values():
        spine.set_visible(False)
    fig.text(0.01, 0.01, "Source: World Bank, World Development Indicators (SH.DYN.MORT).", fontsize=8, color="#6b7280")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUTPUT_DIR / "regional-trends.png", dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    OUTPUT_DIR.mkdir(exist_ok=True)
    frame = load_data()
    table = comparison_table(frame)
    save_comparison(table)
    save_trends(frame)
    table.to_csv(OUTPUT_DIR / "regional-summary.csv", index=False)
    print(table[["region", "rate_1990", "rate_2024", "decline_pct"]].to_string(index=False))


if __name__ == "__main__":
    main()
