import pandas as pd
import pytest

from olist_analysis import clean, metrics, rfm


def tables():
    ts = pd.to_datetime
    orders = pd.DataFrame({
        "order_id": ["o1", "o2", "o3", "o4", "o5"],
        "customer_id": ["c1", "c2", "c3", "c4", "c5"],
        "order_status": ["delivered", "delivered", "canceled", "delivered", "delivered"],
        "order_purchase_timestamp": ts(["2017-03-01", "2017-04-01", "2017-04-02", "2017-04-03", "2017-04-04"]),
        "order_approved_at": ts(["2017-03-01"] * 5),
        "order_delivered_carrier_date": ts(["2017-03-02"] * 5),
        "order_delivered_customer_date": ts(["2017-03-11", "2017-04-20", None, "2017-04-10", "2017-04-09"]),
        "order_estimated_delivery_date": ts(["2017-03-15", "2017-04-10", "2017-04-12", "2017-04-15", "2017-04-15"]),
    })
    customers = pd.DataFrame({"customer_id": ["c1", "c2", "c3", "c4", "c5"],
                              "customer_unique_id": ["u1", "u1", "u2", "u3", "u4"], "customer_state": ["SP"] * 5})
    items = pd.DataFrame({"order_id": ["o1", "o2", "o3", "o4"], "order_item_id": [1, 1, 1, 1],
                          "product_id": ["p1", "p1", "p2", "p2"], "price": [100.0, 50.0, 10.0, 20.0],
                          "freight_value": [10.0] * 4})
    reviews = pd.DataFrame({"order_id": ["o1", "o2"], "review_score": [5, 1]})
    products = pd.DataFrame({"product_id": ["p1", "p2"], "product_category_name": ["beleza", "esporte"]})
    tr = pd.DataFrame({"product_category_name": ["beleza"], "product_category_name_english": ["beauty"]})
    return {"orders": orders, "customers": customers, "items": items, "reviews": reviews,
            "products": products, "translation": tr}


def test_excludes_canceled_and_orders_without_items():
    o = clean.build_orders(tables())
    assert set(o.order_id) == {"o1", "o2", "o4"}          # o3 canceled, o5 has no items


def test_customer_unique_id_links_repeat_buyer():
    o = clean.build_orders(tables())
    assert o.groupby("customer_unique_id").order_id.nunique()["u1"] == 2


def test_late_flag_and_delivery_days():
    o = clean.build_orders(tables()).set_index("order_id")
    assert o.loc["o1", "delivery_days"] == 10 and not o.loc["o1", "is_late"]
    assert bool(o.loc["o2", "is_late"])


def test_category_translation_and_fallback():
    t = tables(); o = clean.build_orders(t); it = clean.build_items(t, o)
    cats = dict(zip(it.product_id, it.category))
    assert cats["p1"] == "beauty" and cats["p2"] == "esporte"      # unmapped category falls back to the original name


def test_monthly_sales_only_full_months():
    o = clean.build_orders(tables())
    m = metrics.monthly_sales(o).set_index("month")
    assert m.loc["2017-03", "revenue"] == 100 and m.loc["2017-04", "orders"] == 2


def test_rfm_repeat_customer_has_frequency_two():
    o = clean.build_orders(tables())
    r = rfm.compute_rfm(o).set_index("customer_unique_id")
    assert r.loc["u1", "frequency"] == 2 and r.loc["u1", "monetary"] == 150


def test_rfm_scores_in_range_and_segments_assigned():
    n = 100
    o = pd.DataFrame({"customer_unique_id": [f"u{i}" for i in range(n)], "order_id": [f"o{i}" for i in range(n)],
                      "order_purchase_timestamp": pd.date_range("2018-01-01", periods=n),
                      "items_value": [float(i + 1) for i in range(n)]})
    r = rfm.compute_rfm(o)
    assert r.R.between(1, 5).all() and r.M.between(1, 5).all()
    assert r.loc[r.recency_days.idxmin(), "R"] == 5 and r.loc[r.monetary.idxmax(), "M"] == 5
    assert r.segment.notna().all()


@pytest.mark.parametrize("F,R,M,exp", [(2, 3, 1, "Loyal"), (3, 1, 5, "Repeat at risk"), (1, 5, 5, "New high-value"),
                                       (1, 4, 2, "New"), (1, 1, 5, "Big spender, lapsed"), (1, 2, 1, "Lapsed"),
                                       (1, 3, 3, "Regular one-time")])
def test_segment_rules(F, R, M, exp):
    assert rfm.segment(pd.Series({"F": F, "R": R, "M": M})) == exp
