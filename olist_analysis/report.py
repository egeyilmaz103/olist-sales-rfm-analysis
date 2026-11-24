"""Write CSV tables and charts."""
from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

BLUE, GREEN, GREY = "#2a6f97", "#6a994e", "#9aa5b1"


def _clean(ax):
    ax.spines[["top", "right"]].set_visible(False)


def chart_monthly(m: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 4), constrained_layout=True)
    ax.bar(m["month"], m["revenue"] / 1e3, color=BLUE)
    ax.set_title("Monthly revenue (item prices), Jan 2017 - Aug 2018")
    ax.set_ylabel("BRL thousand")
    ax.set_xticks(range(0, len(m), 2)); ax.set_xticklabels(m["month"][::2], rotation=45, ha="right")
    _clean(ax); fig.savefig(path, dpi=150); plt.close(fig)


def chart_categories(c: pd.DataFrame, path: Path) -> None:
    c = c.sort_values("revenue")
    fig, ax = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
    ax.barh(c["category"], c["revenue"] / 1e3, color=BLUE)
    for i, v in enumerate(c["revenue_share_pct"]):
        ax.text(c["revenue"].iloc[i] / 1e3, i, f" {v:.1f}%", va="center", fontsize=9)
    ax.set_title("Top categories by revenue (share of total)"); ax.set_xlabel("BRL thousand")
    ax.set_xlim(0, c["revenue"].max() / 1e3 * 1.15)
    _clean(ax); fig.savefig(path, dpi=150); plt.close(fig)


def chart_segments(s: pd.DataFrame, path: Path) -> None:
    s = s.sort_values("customers_pct")
    fig, ax = plt.subplots(figsize=(9, 4.5), constrained_layout=True)
    y = range(len(s)); h = 0.38
    ax.barh([i + h / 2 for i in y], s["customers_pct"], h, color=GREY, label="% of customers")
    ax.barh([i - h / 2 for i in y], s["revenue_pct"], h, color=GREEN, label="% of revenue")
    ax.set_yticks(list(y)); ax.set_yticklabels(s["segment"])
    ax.set_title("RFM segments: share of customers vs. share of revenue"); ax.set_xlabel("%")
    ax.legend(frameon=False); _clean(ax); fig.savefig(path, dpi=150); plt.close(fig)


def write_all(out_dir, monthly, cats, states, reviews, delivery, rfm, seg) -> None:
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    monthly.round(2).to_csv(out / "monthly_sales.csv", index=False)
    cats.round(2).to_csv(out / "top_categories.csv", index=False)
    states.round(2).to_csv(out / "late_delivery_by_state.csv", index=False)
    reviews.round(3).to_csv(out / "review_by_lateness.csv", index=False)
    seg.round(2).to_csv(out / "rfm_segment_summary.csv", index=False)
    rfm.drop(columns=["customer_unique_id"]).describe().round(2).to_csv(out / "rfm_score_distribution.csv")
    (out / "delivery_summary.json").write_text(json.dumps(delivery, indent=2))
    chart_monthly(monthly, out / "monthly_revenue.png")
    chart_categories(cats, out / "top_categories.png")
    chart_segments(seg, out / "rfm_segments.png")
