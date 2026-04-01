import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Manufacturing SPC Dashboard",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Manufacturing SPC Dashboard")
st.markdown("Upload your process data to generate control charts and process capability analysis.")

# ─────────────────────────────────────────────
# SIDEBAR — USER INPUTS
# ─────────────────────────────────────────────
st.sidebar.header("⚙️ Process Settings")

usl = st.sidebar.number_input("Upper Spec Limit (USL)", value=10.10, step=0.01, format="%.3f")
lsl = st.sidebar.number_input("Lower Spec Limit (LSL)", value=9.90, step=0.01, format="%.3f")
target = st.sidebar.number_input("Target / Nominal", value=10.00, step=0.01, format="%.3f")

st.sidebar.markdown("---")
uploaded_file = st.sidebar.file_uploader("📂 Upload CSV File", type=["csv"])
st.sidebar.markdown("CSV must have columns: `subgroup`, `measurement_1` through `measurement_n`")

# ─────────────────────────────────────────────
# LOAD DATA
# ─────────────────────────────────────────────
if uploaded_file is not None:
    df = pd.read_csv(uploaded_file)
    st.sidebar.success(f"✅ Loaded {len(df)} subgroups")
else:
    st.sidebar.info("Using built-in sample data. Upload your own CSV to analyze real data.")
    df = pd.read_csv("sample_data.csv")

# ─────────────────────────────────────────────
# CALCULATE SUBGROUP STATS
# ─────────────────────────────────────────────
# Get only the measurement columns (ignore 'subgroup' column)
measure_cols = [c for c in df.columns if c.startswith("measurement")]
n = len(measure_cols)  # subgroup size

# Xbar = average of each subgroup row
df["Xbar"] = df[measure_cols].mean(axis=1)

# R = range (max - min) within each subgroup row
df["R"] = df[measure_cols].max(axis=1) - df[measure_cols].min(axis=1)

# Grand mean and mean range
X_double_bar = df["Xbar"].mean()
R_bar = df["R"].mean()

# ─────────────────────────────────────────────
# CONTROL CHART CONSTANTS (standard SPC tables)
# ─────────────────────────────────────────────
# These constants depend on subgroup size n
# A2, D3, D4 are from standard SPC control chart constant tables
constants = {
    2:  {"A2": 1.880, "D3": 0,     "D4": 3.267, "d2": 1.128},
    3:  {"A2": 1.023, "D3": 0,     "D4": 2.574, "d2": 1.693},
    4:  {"A2": 0.729, "D3": 0,     "D4": 2.282, "d2": 2.059},
    5:  {"A2": 0.577, "D3": 0,     "D4": 2.114, "d2": 2.326},
    6:  {"A2": 0.483, "D3": 0,     "D4": 2.004, "d2": 2.534},
    7:  {"A2": 0.419, "D3": 0.076, "D4": 1.924, "d2": 2.704},
    8:  {"A2": 0.373, "D3": 0.136, "D4": 1.864, "d2": 2.847},
    9:  {"A2": 0.337, "D3": 0.184, "D4": 1.816, "d2": 2.970},
    10: {"A2": 0.308, "D3": 0.223, "D4": 1.777, "d2": 3.078},
}

if n not in constants:
    st.error(f"Subgroup size {n} not supported. Use 2–10 measurements per subgroup.")
    st.stop()

A2 = constants[n]["A2"]
D3 = constants[n]["D3"]
D4 = constants[n]["D4"]
d2 = constants[n]["d2"]

# ─────────────────────────────────────────────
# CONTROL LIMITS
# ─────────────────────────────────────────────
# X-bar chart limits
UCL_xbar = X_double_bar + A2 * R_bar
LCL_xbar = X_double_bar - A2 * R_bar

# R chart limits
UCL_r = D4 * R_bar
LCL_r = D3 * R_bar

# ─────────────────────────────────────────────
# WESTERN ELECTRIC RULE 1 — Point beyond 3-sigma
# (the most common out-of-control signal)
# ─────────────────────────────────────────────
df["xbar_ooc"] = (df["Xbar"] > UCL_xbar) | (df["Xbar"] < LCL_xbar)
df["r_ooc"]    = (df["R"] > UCL_r) | (df["R"] < LCL_r)

# ─────────────────────────────────────────────
# PROCESS CAPABILITY (Cp, Cpk)
# ─────────────────────────────────────────────
# Sigma estimated from R-bar / d2 (standard method — not sample std dev)
sigma_est = R_bar / d2

# Cp = tolerance spread / process spread
Cp  = (usl - lsl) / (6 * sigma_est)

# Cpk = how centered the process is (lower of upper/lower capability)
Cpu = (usl - X_double_bar) / (3 * sigma_est)
Cpl = (X_double_bar - lsl) / (3 * sigma_est)
Cpk = min(Cpu, Cpl)

# Sigma level (approximate)
sigma_level = Cpk * 3

# ─────────────────────────────────────────────
# SUMMARY METRICS ROW
# ─────────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Grand Mean (X̄̄)", f"{X_double_bar:.4f}")
col2.metric("Cp",  f"{Cp:.3f}",  delta="Capable" if Cp >= 1.33 else "Not Capable",
            delta_color="normal" if Cp >= 1.33 else "inverse")
col3.metric("Cpk", f"{Cpk:.3f}", delta="Capable" if Cpk >= 1.33 else "Not Capable",
            delta_color="normal" if Cpk >= 1.33 else "inverse")
col4.metric("Sigma Level", f"{sigma_level:.2f}σ")
col5.metric("Out-of-Control Points", f"{df['xbar_ooc'].sum()} / {len(df)}")

st.markdown("---")

# ─────────────────────────────────────────────
# CONTROL CHARTS (X-bar and R, side by side)
# ─────────────────────────────────────────────
fig = make_subplots(
    rows=2, cols=1,
    subplot_titles=("X-bar Chart (Subgroup Averages)", "R Chart (Subgroup Ranges)"),
    vertical_spacing=0.12
)

subgroups = df["subgroup"]

# ── X-BAR CHART ──
# In-control points (green)
in_ctrl_x = df[~df["xbar_ooc"]]
fig.add_trace(go.Scatter(
    x=in_ctrl_x["subgroup"], y=in_ctrl_x["Xbar"],
    mode="lines+markers", name="Xbar (In Control)",
    line=dict(color="#2196F3"), marker=dict(size=7)
), row=1, col=1)

# Out-of-control points (red)
ooc_x = df[df["xbar_ooc"]]
if not ooc_x.empty:
    fig.add_trace(go.Scatter(
        x=ooc_x["subgroup"], y=ooc_x["Xbar"],
        mode="markers", name="OUT OF CONTROL",
        marker=dict(color="red", size=12, symbol="x")
    ), row=1, col=1)

# Control limit lines
for val, name, color, dash in [
    (UCL_xbar, "UCL", "red", "dash"),
    (X_double_bar, "X̄̄ (CL)", "green", "solid"),
    (LCL_xbar, "LCL", "red", "dash"),
]:
    fig.add_hline(y=val, line_color=color, line_dash=dash,
                  annotation_text=f"{name}: {val:.4f}",
                  annotation_position="right", row=1, col=1)

# Spec limits (dashed orange)
fig.add_hline(y=usl, line_color="orange", line_dash="dot",
              annotation_text=f"USL: {usl}", row=1, col=1)
fig.add_hline(y=lsl, line_color="orange", line_dash="dot",
              annotation_text=f"LSL: {lsl}", row=1, col=1)

# ── R CHART ──
in_ctrl_r = df[~df["r_ooc"]]
fig.add_trace(go.Scatter(
    x=in_ctrl_r["subgroup"], y=in_ctrl_r["R"],
    mode="lines+markers", name="R (In Control)",
    line=dict(color="#9C27B0"), marker=dict(size=7)
), row=2, col=1)

ooc_r = df[df["r_ooc"]]
if not ooc_r.empty:
    fig.add_trace(go.Scatter(
        x=ooc_r["subgroup"], y=ooc_r["R"],
        mode="markers", name="R Out of Control",
        marker=dict(color="red", size=12, symbol="x")
    ), row=2, col=1)

for val, name, color, dash in [
    (UCL_r, "UCL", "red", "dash"),
    (R_bar, "R̄ (CL)", "green", "solid"),
    (LCL_r, "LCL", "red", "dash"),
]:
    fig.add_hline(y=val, line_color=color, line_dash=dash,
                  annotation_text=f"{name}: {val:.4f}",
                  annotation_position="right", row=2, col=1)

fig.update_layout(height=650, template="plotly_white", showlegend=True)
fig.update_xaxes(title_text="Subgroup Number")
fig.update_yaxes(title_text="Measurement", row=1, col=1)
fig.update_yaxes(title_text="Range", row=2, col=1)

st.plotly_chart(fig, use_container_width=True)

# ─────────────────────────────────────────────
# CAPABILITY INTERPRETATION
# ─────────────────────────────────────────────
st.subheader("📊 Process Capability Summary")

def cpk_interpretation(cpk):
    if cpk >= 1.67: return "✅ Excellent — World class (≥1.67)"
    elif cpk >= 1.33: return "✅ Capable — Meets standard (≥1.33)"
    elif cpk >= 1.00: return "⚠️ Marginal — Improvement needed (1.00–1.33)"
    else: return "❌ Incapable — Process out of spec (<1.00)"

c1, c2 = st.columns(2)
with c1:
    st.markdown(f"""
    | Metric | Value | Benchmark |
    |--------|-------|-----------|
    | USL | {usl} | — |
    | LSL | {lsl} | — |
    | Grand Mean (X̄̄) | {X_double_bar:.4f} | Target: {target} |
    | Estimated Sigma (σ) | {sigma_est:.4f} | — |
    | Cp | {Cp:.3f} | ≥ 1.33 required |
    | Cpk | {Cpk:.3f} | ≥ 1.33 required |
    | Sigma Level | {sigma_level:.2f} | 6σ = world class |
    """)

with c2:
    st.markdown("**Interpretation**")
    st.info(cpk_interpretation(Cpk))
    if Cpk < Cp * 0.95:
        shift_pct = abs(X_double_bar - target) / target * 100
        st.warning(f"⚠️ Process is off-center by ~{shift_pct:.2f}%. Re-centering could improve Cpk significantly.")
    if df["xbar_ooc"].sum() > 0:
        ooc_list = df[df["xbar_ooc"]]["subgroup"].tolist()
        st.error(f"🚨 Out-of-control signals at subgroups: {ooc_list}. Investigate for assignable causes.")
    else:
        st.success("✅ No out-of-control signals detected on X-bar chart.")

# ─────────────────────────────────────────────
# RAW DATA TABLE
# ─────────────────────────────────────────────
with st.expander("📋 View Raw Data Table"):
    display_df = df.copy()
    display_df["Status"] = display_df["xbar_ooc"].apply(lambda x: "🔴 OOC" if x else "🟢 OK")
    st.dataframe(display_df[["subgroup", "Xbar", "R", "Status"]].round(4), use_container_width=True)

st.markdown("---")
st.caption("Built with Python · Streamlit · Plotly | Manufacturing SPC Dashboard — Portfolio Project")
