"""python -m olist_analysis --raw data/raw --out outputs"""
import argparse

from . import clean, load, metrics, report, rfm


def main() -> None:
    p = argparse.ArgumentParser(prog="olist_analysis")
    p.add_argument("--raw", default="data/raw"); p.add_argument("--out", default="outputs")
    a = p.parse_args()
    t = load.load(a.raw)
    orders = clean.build_orders(t)
    items = clean.build_items(t, orders)
    monthly = metrics.monthly_sales(orders)
    cats = metrics.top_categories(items)
    delivery = metrics.delivery_summary(orders)
    states = metrics.late_by_state(orders)
    reviews = metrics.review_by_lateness(orders)
    r = rfm.compute_rfm(orders)
    seg = rfm.segment_summary(r)
    report.write_all(a.out, monthly, cats, states, reviews, delivery, r, seg)
    print(f"Valid orders: {len(orders):,} | customers: {orders.customer_unique_id.nunique():,}")
    print(f"Revenue Jan-2017..Aug-2018: {monthly.revenue.sum():,.0f} BRL")
    print(delivery)
    print(seg[["segment", "customers", "customers_pct", "revenue_pct"]].round(1).to_string(index=False))


main()
