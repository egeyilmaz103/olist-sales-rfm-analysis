"""Build analysis-ready tables from the raw ones.

Decisions (documented because they change the numbers):
* A customer is ``customer_unique_id``. ``customer_id`` is created per order in Olist,
  so using it would make every customer look like a one-time buyer.
* Orders with status ``canceled`` or ``unavailable`` are excluded from sales and RFM.
* Revenue = sum of item prices (freight reported separately). Payment totals differ from
  items + freight in a small share of orders, so they are not used for revenue.
* Only full months are analysed (2017-01 .. 2018-08): 2016 and Sep-Oct 2018 are sparse.
"""
from __future__ import annotations

import pandas as pd

EXCLUDED_STATUSES = {"canceled", "unavailable"}
FULL_MONTHS = ("2017-01", "2018-08")


def build_orders(t: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """One row per valid order with value, delivery and review fields."""
    o = t["orders"].merge(t["customers"][["customer_id", "customer_unique_id", "customer_state"]],
                          on="customer_id", how="left", validate="1:1")
    o = o[~o["order_status"].isin(EXCLUDED_STATUSES)]
    items = t["items"].groupby("order_id").agg(items_value=("price", "sum"), freight_value=("freight_value", "sum"),
                                               n_items=("order_item_id", "count"))
    o = o.merge(items, on="order_id", how="inner")          # drops orders that have no items
    rev = t["reviews"].groupby("order_id")["review_score"].mean().rename("review_score")
    o = o.merge(rev, on="order_id", how="left")
    o["delivery_days"] = (o["order_delivered_customer_date"] - o["order_purchase_timestamp"]).dt.total_seconds() / 86400
    delivered = o["order_delivered_customer_date"].notna()
    o["is_late"] = pd.NA
    o.loc[delivered, "is_late"] = (o.loc[delivered, "order_delivered_customer_date"]
                                   > o.loc[delivered, "order_estimated_delivery_date"])
    o["is_late"] = o["is_late"].astype("boolean")
    o["month"] = o["order_purchase_timestamp"].dt.to_period("M")
    return o.reset_index(drop=True)


def build_items(t: dict[str, pd.DataFrame], orders: pd.DataFrame) -> pd.DataFrame:
    """Item lines of valid orders with English category names."""
    it = t["items"].merge(orders[["order_id", "month"]], on="order_id", how="inner")
    it = it.merge(t["products"][["product_id", "product_category_name"]], on="product_id", how="left")
    it = it.merge(t["translation"], on="product_category_name", how="left")
    it["category"] = it["product_category_name_english"].fillna(it["product_category_name"]).fillna("unknown")
    return it.drop(columns=["product_category_name", "product_category_name_english"])


def full_months(df: pd.DataFrame, col: str = "month") -> pd.DataFrame:
    lo, hi = (pd.Period(x, "M") for x in FULL_MONTHS)
    return df[(df[col] >= lo) & (df[col] <= hi)]
