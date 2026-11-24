"""Read the raw Olist CSV files."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

ORDER_DATES = ["order_purchase_timestamp", "order_approved_at", "order_delivered_carrier_date",
               "order_delivered_customer_date", "order_estimated_delivery_date"]


def load(raw_dir: str | Path) -> dict[str, pd.DataFrame]:
    d = Path(raw_dir)
    need = {
        "orders": "olist_orders_dataset.csv", "customers": "olist_customers_dataset.csv",
        "items": "olist_order_items_dataset.csv", "payments": "olist_order_payments_dataset.csv",
        "reviews": "olist_order_reviews_dataset.csv", "products": "olist_products_dataset.csv",
        "translation": "product_category_name_translation.csv",
    }
    missing = [f for f in need.values() if not (d / f).exists()]
    if missing:
        raise FileNotFoundError(f"Missing files in {d}: {missing}. See README for the download link.")
    t = {k: pd.read_csv(d / f) for k, f in need.items() if k != "orders"}
    t["orders"] = pd.read_csv(d / need["orders"], parse_dates=ORDER_DATES)
    return t
