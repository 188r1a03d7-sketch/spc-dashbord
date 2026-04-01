import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="Door Panel SPC Dashboard | Achyuth Kandoori",
    page_icon="🏭",
    layout="wide"
)

st.title("🏭 Door Panel Thickness — SPC Dashboard")
st.markdown("Upload subgroup measurement data to generate X-bar/R control charts, process capability analysis (Cp, Cpk), and Gauge R&R.")

tab1, tab2 = st.tabs(["📈 SPC & Capability", "🔬 Gauge R&R"])

with tab1:

    st.sidebar.header("⚙️ Process Settings")
    usl    = st.sidebar.number_input("Upper Spec Limit (USL)", value=3.350, step=0.001, format="%.3f")
    lsl    = st.sidebar.number_input("Lower Spec Limit (LSL)", value=3.050, step=0.001, format="%.3f")
    target = st.sidebar.number_input("Target / Nominal",       value=3.200, step=0.001, format="%.3f")
    st.sidebar.markdown("---")
    uploaded_file = st.sidebar.file_uploader("📂 Upload SPC CSV", type=["csv"])
    st.sidebar.markdown("CSV must have columns: `subgroup`, `measurement_1` through `measurement_n`")

    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.sidebar.success(f"✅ Loaded {len(df)} subgroups")
    else:
        st.sidebar.info("Using built-in sample data.")
        df = pd.read_csv("sample_data.csv")

    measure_cols = [c for c in df.columns if c.startswith("measurement")]
    n = len(measure_cols)
    df["Xbar"] = df[measure_cols].mean(axis=1)
    df["R"]    = df[measure_cols].max(axis=1) - df[measure_cols].min(axis=1)
    X_double_bar = df["Xbar"].mean()
    R_bar        = df["R"].mean()

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
        st.error(f"Subgroup size {n} not supported. Use 2-10 measurements per subgroup.")
        st.stop()

    A2 = constants[n]["A2"]
    D3 = constants[n]["D3"]
    D4 = constants[n]["D4"]
    d2 = constants[n]["d2"]

    UCL_xbar = X_double_bar + A2 * R_bar
    LCL_xbar = X_double_bar - A2 * R_bar
    UCL_r    = D4 * R_bar
    LCL_r    = D3 * R_bar

    df["xbar_ooc"] = (df["Xbar"] > UCL_xbar) | (df["Xbar"] < LCL_xbar)
    df["r_ooc"]    = (df["R"] > UCL_r)        | (df["R"] < LCL_r)

    sigma_est   = R_bar / d2
    Cp          = (usl - lsl) / (6 * sigma_est)
    Cpu         = (usl - X_double_bar) / (3 * sigma_est)
    Cpl         = (X_double_bar - lsl) / (3 * sigma_est)
    Cpk         = min(Cpu, Cpl)
    sigma_level = Cpk * 3

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Grand Mean (X-bar-bar)", f"{X_double_bar:.4f}")
    c2.metric("Cp",  f"{Cp:.3f}",  delta="Capable" if Cp  >= 1.33 else "Not Capable", delta_color="normal" if Cp  >= 1.33 else "inverse")
    c3.metric("Cpk", f"{Cpk:.3f}", delta="Capable" if Cpk >= 1.33 else "Not Capable", delta_color="normal" if Cpk >= 1.33 else "inverse")
    c4.metric("Sigma Level", f"{sigma_level:.2f}s")
    c5.metric("Out-of-Control", f"{df['xbar_ooc'].sum()} / {len(df)}")

    st.markdown("---")

    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=("X-bar Chart (Subgroup Averages)", "R Chart (Subgroup Ranges)"),
        vertical_spacing=0.25,
        row_heights=[0.6, 0.4]
    )

    in_ctrl_x = df[~df["xbar_ooc"]]
    ooc_x     = df[df["xbar_ooc"]]
    in_ctrl_r = df[~df["r_ooc"]]
    ooc_r     = df[df["r_ooc"]]

    fig.add_trace(go.Scatter(
        x=in_ctrl_x["subgroup"], y=in_ctrl_x["Xbar"],
        mode="lines+markers", name="Xbar (In Control)",
        line=dict(color="#2196F3", width=1.5), marker=dict(size=6)
    ), row=1, col=1)

    if not ooc_x.empty:
        fig.add_trace(go.Scatter(
            x=ooc_x["subgroup"], y=ooc_x["Xbar"],
            mode="markers", name="OUT OF CONTROL",
            marker=dict(color="red", size=12, symbol="x-thin", line=dict(width=2.5))
        ), row=1, col=1)

    for val, label, color, dash in [
        (UCL_xbar, f"UCL: {UCL_xbar:.4f}", "red",     "dash"),
        (X_double_bar, f"CL: {X_double_bar:.4f}", "#1D9E75", "solid"),
        (LCL_xbar, f"LCL: {LCL_xbar:.4f}", "red",     "dash"),
    ]:
        fig.add_hline(y=val, line_color=color, line_dash=dash,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=10, row=1, col=1)

    fig.add_hline(y=usl, line_color="orange", line_dash="dot",
                  annotation_text=f"USL: {usl}", annotation_position="right",
                  annotation_font_size=10, row=1, col=1)
    fig.add_hline(y=lsl, line_color="orange", line_dash="dot",
                  annotation_text=f"LSL: {lsl}", annotation_position="right",
                  annotation_font_size=10, row=1, col=1)

    fig.add_trace(go.Scatter(
        x=in_ctrl_r["subgroup"], y=in_ctrl_r["R"],
        mode="lines+markers", name="R (In Control)",
        line=dict(color="#9C27B0", width=1.5), marker=dict(size=6)
    ), row=2, col=1)

    if not ooc_r.empty:
        fig.add_trace(go.Scatter(
            x=ooc_r["subgroup"], y=ooc_r["R"],
            mode="markers", name="R Out of Control",
            marker=dict(color="red", size=12, symbol="x-thin", line=dict(width=2.5))
        ), row=2, col=1)

    for val, label, color, dash in [
        (UCL_r, f"UCL: {UCL_r:.4f}", "red",     "dash"),
        (R_bar, f"Rbar: {R_bar:.4f}", "#1D9E75", "solid"),
    ]:
        fig.add_hline(y=val, line_color=color, line_dash=dash,
                      annotation_text=label, annotation_position="right",
                      annotation_font_size=10, row=2, col=1)

    fig.update_layout(
        height=750, template="plotly_white", showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        margin=dict(r=120)
    )
    fig.update_xaxes(title_text="Subgroup Number", row=1, col=1)
    fig.update_xaxes(title_text="Subgroup Number", row=2, col=1)
    fig.update_yaxes(title_text="Measurement (mm)", row=1, col=1)
    fig.update_yaxes(title_text="Range (mm)",        row=2, col=1)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Process Capability Summary")

    def cpk_label(cpk):
        if cpk >= 1.67:  return "Excellent - World class (>=1.67)"
        elif cpk >= 1.33: return "Capable - Meets AIAG standard (>=1.33)"
        elif cpk >= 1.00: return "Marginal - Improvement needed (1.00-1.33)"
        else:             return "Incapable - Process does not meet spec (<1.00)"

    ca1, ca2 = st.columns(2)
    with ca1:
        st.markdown(f"""
| Metric | Value | Benchmark |
|--------|-------|-----------|
| USL | {usl:.3f} mm | - |
| LSL | {lsl:.3f} mm | - |
| Tolerance | {usl-lsl:.3f} mm | - |
| Grand Mean | {X_double_bar:.4f} mm | Target: {target:.3f} mm |
| Est. Sigma (R-bar/d2) | {sigma_est:.4f} mm | - |
| Cp | {Cp:.3f} | >=1.33 required |
| Cpu | {Cpu:.3f} | Upper capability |
| Cpl | {Cpl:.3f} | Lower capability |
| Cpk | {Cpk:.3f} | >=1.33 required |
| Sigma Level | {sigma_level:.2f} | 6s = world class |
        """)
    with ca2:
        st.markdown("**Interpretation**")
        st.info(cpk_label(Cpk))
        if Cpk < Cp * 0.95:
            shift = abs(X_double_bar - target)
            st.warning(f"Process is off-center by {shift:.4f} mm. Re-centering toward {target:.3f} mm would improve Cpk.")
        if df["xbar_ooc"].sum() > 0:
            ooc_list = df[df["xbar_ooc"]]["subgroup"].tolist()
            st.error(f"Out-of-control signals at subgroups: {ooc_list}. Investigate for assignable causes.")
        else:
            st.success("No out-of-control signals detected. Process is statistically stable.")
        st.markdown("> **Note:** UCL/LCL are statistical control limits from process data. USL/LSL are engineering spec limits. A point can be out of control but still within spec - SPC detects process shifts before defects occur.")

    with st.expander("View Raw Data Table"):
        display_df = df.copy()
        display_df["Status"] = display_df["xbar_ooc"].apply(lambda x: "OOC" if x else "OK")
        st.dataframe(display_df[["subgroup", "Xbar", "R", "Status"]].round(4), use_container_width=True)


with tab2:

    st.subheader("Gauge R&R Analysis")
    st.markdown("Evaluate measurement system variation using three AIAG-standard methods.")

    st.info("Upload a CSV with columns: `part`, `operator`, `trial`, `measurement`")

    grr_file = st.file_uploader("Upload Gauge R&R CSV", type=["csv"], key="grr")

    np.random.seed(7)
    parts_s     = list(range(1, 11)) * 6
    operators_s = ["Op1"]*20 + ["Op2"]*20 + ["Op3"]*20
    trials_s    = ([1]*10 + [2]*10) * 3
    true_vals   = {p: 3.200 + np.random.uniform(-0.08, 0.08) for p in range(1, 11)}
    meas_s = []
    for p, op, t in zip(parts_s, operators_s, trials_s):
        bias = {"Op1": 0.000, "Op2": 0.004, "Op3": -0.003}[op]
        meas_s.append(round(true_vals[p] + bias + np.random.normal(0, 0.008), 4))
    sample_grr = pd.DataFrame({"part": parts_s, "operator": operators_s, "trial": trials_s, "measurement": meas_s})
    sample_grr = sample_grr.sort_values(["operator", "part", "trial"]).reset_index(drop=True)

    if grr_file is not None:
        grr_df = pd.read_csv(grr_file)
        st.success(f"Loaded {len(grr_df)} rows")
    else:
        grr_df = sample_grr

    required = {"part", "operator", "trial", "measurement"}
    if not required.issubset(grr_df.columns):
        st.error(f"CSV must contain columns: {required}")
        st.stop()

    operators_list = sorted(grr_df["operator"].unique())
    parts_list     = sorted(grr_df["part"].unique())
    n_op   = len(operators_list)
    n_part = len(parts_list)
    n_rep  = int(grr_df.groupby(["operator", "part"]).size().max())

    grr_usl   = st.number_input("USL for tolerance calculation", value=3.350, step=0.001, format="%.3f", key="grr_usl")
    grr_lsl   = st.number_input("LSL for tolerance calculation", value=3.050, step=0.001, format="%.3f", key="grr_lsl")
    tolerance = grr_usl - grr_lsl

    st.markdown("---")

    # ── METHOD 1 — RANGE ──
    st.markdown("### Method 1 — Range Method (AIAG short form)")
    st.markdown("Quickest estimate. Measures repeatability only using average range across all operator-part combinations.")

    ranges_grr = grr_df.groupby(["operator","part"])["measurement"].apply(lambda x: x.max()-x.min()).reset_index()
    ranges_grr.columns = ["operator","part","range"]
    Rbar_grr = ranges_grr["range"].mean()
    d2_star  = {2:1.128, 3:1.693, 4:2.059, 5:2.326}.get(n_rep, 1.693)
    EV_range = Rbar_grr / d2_star
    GRR_range = 5.15 * EV_range
    pct_tol_range = (GRR_range / tolerance) * 100

    r1, r2, r3, r4 = st.columns(4)
    r1.metric("R-bar (mean range)", f"{Rbar_grr:.4f} mm")
    r2.metric("EV sigma (Repeatability)", f"{EV_range:.4f} mm")
    r3.metric("GRR Spread (5.15s)", f"{GRR_range:.4f} mm")
    r4.metric("%Tolerance", f"{pct_tol_range:.1f}%",
              delta="Acceptable" if pct_tol_range<=10 else ("Marginal" if pct_tol_range<=30 else "Unacceptable"),
              delta_color="normal" if pct_tol_range<=10 else "inverse")

    st.markdown(f"""
| Item | Calculation | Result |
|------|-------------|--------|
| R-bar | Average of all within-cell ranges | {Rbar_grr:.4f} mm |
| d2* constant (n={n_rep} reps) | From AIAG MSA table | {d2_star} |
| EV sigma | R-bar / d2* = {Rbar_grr:.4f} / {d2_star} | {EV_range:.4f} mm |
| GRR spread | 5.15 x EV | {GRR_range:.4f} mm |
| Tolerance | USL - LSL | {tolerance:.3f} mm |
| %Tolerance | (GRR / Tolerance) x 100 | {pct_tol_range:.1f}% |
    """)

    st.markdown("---")

    # ── METHOD 2 — AVG & RANGE ──
    st.markdown("### Method 2 — Average & Range Method (AIAG standard)")
    st.markdown("Separates Repeatability (EV) and Reproducibility (AV). Standard method from AIAG MSA manual.")

    EV       = Rbar_grr / d2_star
    op_means = grr_df.groupby("operator")["measurement"].mean()
    Xdiff    = op_means.max() - op_means.min()
    d2_op    = {2:1.128, 3:1.693, 4:2.059, 5:2.326}.get(n_op, 1.693)
    AV_raw   = Xdiff / d2_op
    AV_sq    = (AV_raw**2) - ((EV**2) / (n_part * n_rep))
    AV       = np.sqrt(max(AV_sq, 0))
    GRR_av   = np.sqrt(EV**2 + AV**2)

    part_means  = grr_df.groupby("part")["measurement"].mean()
    Rp          = part_means.max() - part_means.min()
    d2_part_tbl = {2:1.128,3:1.693,4:2.059,5:2.326,6:2.534,7:2.704,8:2.847,9:2.970,10:3.078}
    d2_part     = d2_part_tbl.get(n_part, 3.078)
    PV          = Rp / d2_part
    TV          = np.sqrt(GRR_av**2 + PV**2)

    pct_EV  = (EV/TV*100)     if TV>0 else 0
    pct_AV  = (AV/TV*100)     if TV>0 else 0
    pct_GRR = (GRR_av/TV*100) if TV>0 else 0
    pct_PV  = (PV/TV*100)     if TV>0 else 0
    pct_tol_GRR = (5.15*GRR_av/tolerance)*100

    co1, co2, co3, co4, co5 = st.columns(5)
    co1.metric("EV (Repeatability)", f"{EV:.4f} mm")
    co2.metric("AV (Reproducibility)", f"{AV:.4f} mm")
    co3.metric("GRR", f"{GRR_av:.4f} mm")
    co4.metric("%GRR / TV", f"{pct_GRR:.1f}%",
               delta="Acceptable" if pct_GRR<=10 else ("Marginal" if pct_GRR<=30 else "Unacceptable"),
               delta_color="normal" if pct_GRR<=10 else "inverse")
    co5.metric("%Tolerance", f"{pct_tol_GRR:.1f}%")

    st.markdown(f"""
| Source | Sigma | % of Total Variation | % of Tolerance |
|--------|-------|----------------------|----------------|
| Repeatability (EV) | {EV:.4f} mm | {pct_EV:.1f}% | {(5.15*EV/tolerance)*100:.1f}% |
| Reproducibility (AV) | {AV:.4f} mm | {pct_AV:.1f}% | {(5.15*AV/tolerance)*100:.1f}% |
| **GRR combined** | **{GRR_av:.4f} mm** | **{pct_GRR:.1f}%** | **{pct_tol_GRR:.1f}%** |
| Part Variation (PV) | {PV:.4f} mm | {pct_PV:.1f}% | - |
| Total Variation (TV) | {TV:.4f} mm | 100% | - |
    """)

    if pct_GRR <= 10:
        st.success(f"Avg & Range: %GRR = {pct_GRR:.1f}% - ACCEPTABLE (< 10%)")
    elif pct_GRR <= 30:
        st.warning(f"Avg & Range: %GRR = {pct_GRR:.1f}% - MARGINAL (10-30%)")
    else:
        st.error(f"Avg & Range: %GRR = {pct_GRR:.1f}% - UNACCEPTABLE (> 30%)")

    fig_grr = go.Figure()
    fig_grr.add_trace(go.Bar(name="Repeatability (EV)", x=["Variation Breakdown"], y=[pct_EV], marker_color="#2196F3"))
    fig_grr.add_trace(go.Bar(name="Reproducibility (AV)", x=["Variation Breakdown"], y=[pct_AV], marker_color="#FF9800"))
    fig_grr.add_trace(go.Bar(name="Part Variation (PV)", x=["Variation Breakdown"], y=[pct_PV], marker_color="#4CAF50"))
    fig_grr.update_layout(barmode="stack", height=300, template="plotly_white",
                          title="% Contribution to Total Variation",
                          yaxis_title="% of Total Variation",
                          legend=dict(orientation="h", y=-0.3))
    st.plotly_chart(fig_grr, use_container_width=True)

    st.markdown("---")

    # ── METHOD 3 — ANOVA ──
    st.markdown("### Method 3 — ANOVA Method (most accurate)")
    st.markdown("Uses Analysis of Variance to isolate Part, Operator, and Interaction effects. AIAG MSA 4th Edition preferred method.")

    grand_mean = grr_df["measurement"].mean()
    N_total    = len(grr_df)

    part_means_a = grr_df.groupby("part")["measurement"].mean()
    SS_part = (n_op * n_rep) * ((part_means_a - grand_mean)**2).sum()
    df_part = n_part - 1

    op_means_a = grr_df.groupby("operator")["measurement"].mean()
    SS_op   = (n_part * n_rep) * ((op_means_a - grand_mean)**2).sum()
    df_op   = n_op - 1

    cell_means  = grr_df.groupby(["part","operator"])["measurement"].mean()
    SS_cells    = n_rep * ((cell_means - grand_mean)**2).sum()
    SS_inter    = SS_cells - SS_part - SS_op
    df_inter    = df_part * df_op

    SS_error = 0
    for (p, op), group in grr_df.groupby(["part","operator"]):
        SS_error += ((group["measurement"] - group["measurement"].mean())**2).sum()
    df_error  = n_part * n_op * (n_rep - 1)
    SS_total  = SS_part + SS_op + SS_inter + SS_error
    df_total  = N_total - 1

    MS_part  = SS_part  / df_part  if df_part  > 0 else 0
    MS_op    = SS_op    / df_op    if df_op    > 0 else 0
    MS_inter = SS_inter / df_inter if df_inter > 0 else 0
    MS_error = SS_error / df_error if df_error > 0 else 0

    F_part  = MS_part  / MS_inter if MS_inter > 0 else 0
    F_op    = MS_op    / MS_inter if MS_inter > 0 else 0
    F_inter = MS_inter / MS_error if MS_error > 0 else 0

    var_error = MS_error
    var_inter = max((MS_inter - MS_error) / n_rep, 0)
    var_op    = max((MS_op - MS_inter) / (n_part * n_rep), 0)
    var_part  = max((MS_part - MS_inter) / (n_op * n_rep), 0)

    var_repeatability   = var_error
    var_reproducibility = var_op + var_inter
    var_grr             = var_repeatability + var_reproducibility
    var_total           = var_grr + var_part

    sigma_repeat  = np.sqrt(var_repeatability)
    sigma_reprod  = np.sqrt(var_reproducibility)
    sigma_grr_an  = np.sqrt(var_grr)
    sigma_part_an = np.sqrt(var_part)
    sigma_total   = np.sqrt(var_total)

    pct_repeat_a = (var_repeatability   / var_total * 100) if var_total > 0 else 0
    pct_reprod_a = (var_reproducibility / var_total * 100) if var_total > 0 else 0
    pct_grr_a    = (var_grr             / var_total * 100) if var_total > 0 else 0
    pct_part_a   = (var_part            / var_total * 100) if var_total > 0 else 0
    pct_tol_a    = (5.15 * sigma_grr_an / tolerance) * 100

    st.markdown("**ANOVA Table:**")
    anova_tbl = pd.DataFrame({
        "Source":  ["Part", "Operator", "Part x Operator", "Repeatability (Error)", "Total"],
        "SS":      [f"{SS_part:.6f}", f"{SS_op:.6f}", f"{SS_inter:.6f}", f"{SS_error:.6f}", f"{SS_total:.6f}"],
        "df":      [df_part, df_op, df_inter, df_error, df_total],
        "MS":      [f"{MS_part:.6f}", f"{MS_op:.6f}", f"{MS_inter:.6f}", f"{MS_error:.6f}", "-"],
        "F ratio": [f"{F_part:.3f}", f"{F_op:.3f}", f"{F_inter:.3f}", "-", "-"],
    })
    st.dataframe(anova_tbl, use_container_width=True, hide_index=True)

    st.markdown("**Variance Components:**")
    vc_tbl = pd.DataFrame({
        "Source":         ["Repeatability (EV)", "Reproducibility (AV)", "GRR", "Part Variation (PV)", "Total"],
        "Variance":       [f"{var_repeatability:.6f}", f"{var_reproducibility:.6f}", f"{var_grr:.6f}", f"{var_part:.6f}", f"{var_total:.6f}"],
        "Sigma":          [f"{sigma_repeat:.4f}", f"{sigma_reprod:.4f}", f"{sigma_grr_an:.4f}", f"{sigma_part_an:.4f}", f"{sigma_total:.4f}"],
        "% Contribution": [f"{pct_repeat_a:.1f}%", f"{pct_reprod_a:.1f}%", f"{pct_grr_a:.1f}%", f"{pct_part_a:.1f}%", "100%"],
        "% Tolerance":    [f"{(5.15*sigma_repeat/tolerance)*100:.1f}%", f"{(5.15*sigma_reprod/tolerance)*100:.1f}%", f"{pct_tol_a:.1f}%", "-", "-"],
    })
    st.dataframe(vc_tbl, use_container_width=True, hide_index=True)

    an1, an2, an3 = st.columns(3)
    an1.metric("GRR sigma (ANOVA)", f"{sigma_grr_an:.4f} mm")
    an2.metric("%GRR / Total Var",  f"{pct_grr_a:.1f}%",
               delta="Acceptable" if pct_grr_a<=10 else ("Marginal" if pct_grr_a<=30 else "Unacceptable"),
               delta_color="normal" if pct_grr_a<=10 else "inverse")
    an3.metric("%Tolerance (ANOVA)", f"{pct_tol_a:.1f}%")

    if pct_grr_a <= 10:
        st.success(f"ANOVA %GRR = {pct_grr_a:.1f}% - Measurement system ACCEPTABLE")
    elif pct_grr_a <= 30:
        st.warning(f"ANOVA %GRR = {pct_grr_a:.1f}% - Measurement system MARGINAL")
    else:
        st.error(f"ANOVA %GRR = {pct_grr_a:.1f}% - Measurement system UNACCEPTABLE")

    st.markdown("---")
    st.markdown("### Method Comparison Summary")
    st.markdown(f"""
| Method | GRR Spread | %Tolerance | %Total Var | Verdict |
|--------|-----------|------------|------------|---------|
| Range Method | {GRR_range:.4f} mm | {pct_tol_range:.1f}% | - | {"Acceptable" if pct_tol_range<=10 else "Marginal" if pct_tol_range<=30 else "Unacceptable"} |
| Avg & Range Method | {5.15*GRR_av:.4f} mm | {pct_tol_GRR:.1f}% | {pct_GRR:.1f}% | {"Acceptable" if pct_GRR<=10 else "Marginal" if pct_GRR<=30 else "Unacceptable"} |
| ANOVA Method | {5.15*sigma_grr_an:.4f} mm | {pct_tol_a:.1f}% | {pct_grr_a:.1f}% | {"Acceptable" if pct_grr_a<=10 else "Marginal" if pct_grr_a<=30 else "Unacceptable"} |
    """)
    st.markdown("> **ANOVA is the most accurate** — it isolates the Part x Operator interaction that the other two methods combine or miss. AIAG MSA 4th Edition recommends ANOVA as the preferred method.")

    with st.expander("View Raw Gauge R&R Data"):
        st.dataframe(grr_df, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("Built by Achyuth Kandoori | Quality Engineer | M.S. Mechanical Engineering, Clemson University | ASQ Lean Six Sigma Green Belt")
