"""Business metrics: sales trend, categories, delivery, reviews."""
from __future__ import annotations

import pandas as pd

from .clean import full_months


def monthly_sales(orders: pd.DataFrame) -> pd.DataFrame:
    o = full_months(orders)
    m = o.groupby("month").agg(orders=("order_id", "nunique"), revenue=("items_value", "sum"),
                               customers=("customer_unique_id", "nunique")).reset_index()
    m["avg_order_value"] = m["revenue"] / m["orders"]
    m["revenue_mom_pct"] = m["revenue"].pct_change() * 100
    m["month"] = m["month"].astype(str)
    return m


def top_categories(items: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    it = full_months(items)
    c = it.groupby("category").agg(revenue=("price", "sum"), items_sold=("price", "size")).sort_values("revenue", ascending=False)
    c["revenue_share_pct"] = c["revenue"] / c["revenue"].sum() * 100
    c["cumulative_share_pct"] = c["revenue_share_pct"].cumsum()
    return c.head(n).reset_index()


def delivery_summary(orders: pd.DataFrame) -> dict:
    d = full_months(orders)
    d = d[d["order_status"] == "delivered"].dropna(subset=["delivery_days", "is_late"])
    return {"delivered_orders": int(len(d)), "median_delivery_days": float(d["delivery_days"].median()),
            "mean_delivery_days": float(d["delivery_days"].mean()), "late_rate_pct": float(d["is_late"].astype(float).mean() * 100)}


def late_by_state(orders: pd.DataFrame, min_orders: int = 500) -> pd.DataFrame:
    d = full_months(orders)
    d = d[d["order_status"] == "delivered"].dropna(subset=["delivery_days", "is_late"])
    g = d.groupby("customer_state").agg(orders=("order_id", "size"), median_days=("delivery_days", "median"),
                                        late_rate_pct=("is_late", lambda s: s.astype(float).mean() * 100))
    return g[g["orders"] >= min_orders].sort_values("late_rate_pct", ascending=False).reset_index()


def review_by_lateness(orders: pd.DataFrame) -> pd.DataFrame:
    d = full_months(orders)
    d = d[d["order_status"] == "delivered"].dropna(subset=["review_score", "is_late"])
    g = d.groupby(d["is_late"].astype(bool)).agg(orders=("order_id", "size"), avg_review=("review_score", "mean")).reset_index()
    g["is_late"] = g["is_late"].map({True: "late", False: "on time"})
    return g
