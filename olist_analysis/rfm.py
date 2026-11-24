"""RFM customer segmentation.

Only ~3% of Olist customers buy more than once, so a textbook 5x5x5 RFM would put almost
everyone in the same frequency bucket. Frequency is therefore scored by rule (1, 2, 3+ orders)
while Recency and Monetary use quintiles.
"""
from __future__ import annotations

import pandas as pd


def _quintile(s: pd.Series, ascending: bool) -> pd.Series:
    """Score 1-5 by rank; 5 is best. Rank first so ties never break the bins."""
    r = s.rank(method="first", ascending=ascending)
    return pd.qcut(r, 5, labels=[1, 2, 3, 4, 5]).astype(int)


def segment(row) -> str:
    if row.F >= 2:
        return "Loyal" if row.R >= 3 else "Repeat at risk"
    if row.R >= 4:
        return "New high-value" if row.M >= 4 else "New"
    if row.R <= 2:
        return "Big spender, lapsed" if row.M >= 4 else "Lapsed"
    return "Regular one-time"


def compute_rfm(orders: pd.DataFrame, snapshot: pd.Timestamp | None = None) -> pd.DataFrame:
    snapshot = snapshot or (orders["order_purchase_timestamp"].max().normalize() + pd.Timedelta(days=1))
    g = orders.groupby("customer_unique_id").agg(last=("order_purchase_timestamp", "max"),
                                                 frequency=("order_id", "nunique"), monetary=("items_value", "sum"))
    g["recency_days"] = (snapshot - g["last"]).dt.days
    g["R"] = _quintile(g["recency_days"], ascending=False)    # fewer days -> higher score
    g["F"] = g["frequency"].clip(upper=3)
    g["M"] = _quintile(g["monetary"], ascending=True)
    g["segment"] = g.apply(segment, axis=1)
    return g.drop(columns="last").reset_index()


def segment_summary(rfm: pd.DataFrame) -> pd.DataFrame:
    s = rfm.groupby("segment").agg(customers=("customer_unique_id", "size"), avg_recency_days=("recency_days", "mean"),
                                   avg_orders=("frequency", "mean"), total_revenue=("monetary", "sum"),
                                   avg_revenue=("monetary", "mean")).reset_index()
    s["customers_pct"] = s["customers"] / s["customers"].sum() * 100
    s["revenue_pct"] = s["total_revenue"] / s["total_revenue"].sum() * 100
    return s.sort_values("total_revenue", ascending=False).reset_index(drop=True)
