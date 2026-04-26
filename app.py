import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NYC Airbnb Pricing Experiment",
    page_icon="🏠",
    layout="wide",
)

# ── Custom CSS ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600&family=DM+Serif+Display&display=swap');
 
    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
    }
    h1, h2, h3 {
        font-family: 'DM Serif Display', serif;
    }
    .metric-card {
        background: #f8f9fb;
        border-radius: 12px;
        padding: 16px 20px;
        border: 1px solid #e8eaed;
    }
    .insight-box {
        background: #eef6ff;
        border-left: 4px solid #2563eb;
        border-radius: 0 8px 8px 0;
        padding: 14px 18px;
        margin: 12px 0;
        font-size: 0.95rem;
        color: #1e3a5f;
    }
    .section-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7280;
        margin-bottom: 4px;
    }
</style>
""", unsafe_allow_html=True)
 
# ── Data ──────────────────────────────────────────────────────────────────────
eligible = pd.read_csv("airbnb_simulation_results.csv")

COLORS = {
    "control":       "#94a3b8",
    "5%_reduction":  "#60a5fa",
    "10%_reduction": "#2563eb",
    "15%_reduction": "#1e3a5f",
}
 
LABEL_MAP = {
    "control":       "0%",
    "5%_reduction":  "5%",
    "10%_reduction": "10%",
    "15%_reduction": "15%",
}
REVERSE_MAP = {v: k for k, v in LABEL_MAP.items()}
ORDER = ["control", "5%_reduction", "10%_reduction", "15%_reduction"]

# ── Header ────────────────────────────────────────────────────────────────────

st.title("NYC Airbnb Pricing Experiment")
st.markdown("#### Do price cuts actually increase revenue?")

st.markdown("""
**Key Takeaway:**  
Price cuts increase predicted demand, but they do not always improve revenue. Broad discounts reduce revenue overall, while private room listings show a stronger response to moderate discounts.""")

st.markdown("""
<div class="insight-box">
<strong>Key finding:</strong> Price cuts increase predicted demand, but they do not always improve revenue.
Broad discounts reduce revenue overall — however, <strong>private room listings</strong> show a meaningful
positive response to moderate (10%) discounts, yielding an estimated <strong>+2.5% revenue gain</strong>.
</div> """, unsafe_allow_html=True)

st.caption("Results are based on a simulated pricing experiment using a predictive demand model.")
st.caption("Data Source: https://www.kaggle.com/datasets/dgomonov/new-york-city-airbnb-open-data")

st.divider()

# ── Sidebar filters ───────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown("### Filters")
    borough = st.selectbox("Borough", ["All"] + sorted(eligible["neighbourhood_group"].unique()))
    room    = st.selectbox("Room Type", ["All"] + sorted(eligible["room_type"].unique()))
    st.divider()
    st.markdown("### Scenario")
    group_display  = st.selectbox("Price Reduction", ["0%", "5%", "10%", "15%"])
    group_selected = REVERSE_MAP[group_display]

# ── Filter data ───────────────────────────────────────────────────────────────

df = eligible.copy()
if borough != "All":
    df = df[df["neighbourhood_group"] == borough]
if room != "All":
    df = df[df["room_type"] == room]
 
summary = (
    df.groupby("group")
    .agg(avg_price=("price","mean"),
         avg_demand=("predicted_high_demand_prob","mean"),
         avg_revenue=("revenue_proxy","mean"))
    .reset_index())

summary["group"] = pd.Categorical(summary["group"], categories=ORDER, ordered=True)
summary = summary.sort_values("group")
 
control_revenue = summary.loc[summary["group"] == "control", "avg_revenue"].iloc[0]
summary["revenue_change_pct"] = (summary["avg_revenue"] - control_revenue) / control_revenue * 100
 
x_labels     = [LABEL_MAP[g] for g in summary["group"]]
bar_colors   = [COLORS[g] for g in summary["group"]]
selected_row = summary.loc[summary["group"] == group_selected].iloc[0]
 
# ── Scenario summary metrics ──────────────────────────────────────────────────

st.subheader("Scenario Summary")
st.markdown(f"Showing results for a **{group_display} price reduction** · {borough} · {room}")

col0, col1, col2, col3 = st.columns(4)
col0.metric("Avg. Listed Price",   f"${selected_row['avg_price']:.2f}")
col1.metric("Predicted Demand",    f"{selected_row['avg_demand']:.3f}",
            help="Probability of a listing receiving a booking, estimated by the demand model.")
col2.metric("Avg. Revenue / Night", f"${selected_row['avg_revenue']:.2f}",
            help="Price x predicted demand probability, used as a revenue approximation.")
col3.metric("Revenue vs. 0% baseline", f"{selected_row['revenue_change_pct']:+.2f}%")


if room == "Private room" and group_selected == "10%_reduction":
    st.success("This is the sweet spot: private room listings at a 10% discount show the strongest positive revenue impact (~+2.5%).")
elif room == "Private room":
    st.info("Private room listings are more price-sensitive than other room types — try the 10% reduction to see the optimal scenario.")
 
st.divider()

# ── Charts ────────────────────────────────────────────────────────────────────

col_left, col_gap, col_right = st.columns([10,1,10])
 
with col_left:
    fig1 = go.Figure(go.Bar(
        x=x_labels,
        y=summary["avg_demand"],
        marker_color=bar_colors,
        hovertemplate="Price reduction: %{x}<br>Avg demand: %{y:.4f}<extra></extra>",
    ))
    fig1.add_hline(y=0, line_color="#374151", line_width=2)
    fig1.update_layout(
        title="Predicted Demand by Price Reduction",
        xaxis_title="Price Reduction (%)",
        yaxis_title="Avg. Predicted Demand Probability",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="DM Sans"),
        title_font=dict(family="DM Serif Display", size=18),
        showlegend=False,
        yaxis=dict(gridcolor="#e8eaed"),
        margin=dict(t=50, b=40))
    st.plotly_chart(fig1, use_container_width=True)
    st.caption("Demand increases as prices fall, but the gain varies by borough and room type.")
 
with col_right:
    rev_colors = ["#4D79DA" if v >= 0 else "#ef4444" for v in summary["revenue_change_pct"]]
    fig2 = go.Figure(go.Bar(
        x=x_labels,
        y=summary["revenue_change_pct"],
        marker_color=rev_colors,
        hovertemplate="Price reduction: %{x}<br>Revenue change: %{y:.2f}%<extra></extra>",
    ))
    fig2.add_hline(y=0, line_color="#374151", line_width=2)
    fig2.update_layout(
        title="Revenue Change vs. 0% Baseline",
        xaxis_title="Price Reduction (%)",
        yaxis_title="Revenue Change (%)",
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="DM Sans"),
        title_font=dict(family="DM Serif Display", size=18),
        showlegend=False,
        yaxis=dict(gridcolor="#e8eaed"),
        margin=dict(t=50, b=40),)
    st.plotly_chart(fig2, use_container_width=True)
    st.caption("Blue bars = revenue gain vs. baseline. Red bars = revenue loss. Positive values mean demand gains outweighed the lower price.")
 
st.divider()


# ── Results & Recommendation ──────────────────────────────────────────────────
st.subheader("Takeaways & Recommendation")
 
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("""
**What the data shows:**
- Demand rises with every discount level
- Overall revenue still declines with broad price cuts
- Private room listings are more price-sensitive
- A 10% discount on private rooms yields ~+2.5% revenue
- Beyond 10%, diminishing demand gains erode revenue further
""")
with col_b:
    st.markdown("""
**Recommendation:**
 
Blanket price reductions are not an effective strategy. While discounts attract more interest, they rarely generate enough additional bookings to offset the lower price.
 
The exception: **private room hosts** may benefit from a targeted **10% reduction**, where price sensitivity is strong enough that the demand uplift more than compensates for the discount.
""")
 
st.divider()

# ── Methodology ───────────────────────────────────────────────────────────────
st.subheader("Methodology")
st.markdown("""
- Demand estimated using a **Random Forest classifier** trained on listing features (price, location, minimum nights, room type, reviews, availability)
- Review count used as a proxy for realized demand
- Revenue approximated as **price × predicted demand probability**
- Price reductions of 5%, 10%, and 15% applied to baseline prices and run through the demand model
- Results are **modeled estimates**, not observed experimental outcomes — causal interpretation requires further study
""")
 

