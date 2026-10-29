"""Figures 1-5 for the v4 manuscript (300 dpi, larger fonts). Reads sol_results.json and data/; writes ../figures/."""
import os, json, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
from matplotlib import rcParams
from matplotlib.lines import Line2D
rcParams["font.family"] = "serif"; rcParams["font.serif"] = ["Times New Roman", "DejaVu Serif"]; rcParams["font.size"] = 11
rcParams["axes.labelsize"] = 11; rcParams["xtick.labelsize"] = 10; rcParams["ytick.labelsize"] = 10; rcParams["legend.fontsize"] = 9
NAVY, PETROL, GOLD, GREY, RED, BLUE2 = "#1C4076", "#007A88", "#B8860B", "#555E66", "#A23B3B", "#5B7DB1"
HERE = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(HERE, "figures"); os.makedirs(OUT, exist_ok=True)
R = json.load(open(f"{HERE}/sol_results.json")); px = pd.read_csv(f"{HERE}/data/prices_aligned.csv", index_col=0, parse_dates=True)
r = pd.read_csv(f"{HERE}/data/daily_returns.csv", index_col=0, parse_dates=True); PJ = json.load(open(f"{HERE}/ports.json")); PORTS, WIN = PJ["PORTS"], PJ["WINDOW"]
names = list(R["ports"].keys()); short = [n.replace(" (US)", " US").replace(" representative", "").replace(" insurer", "").replace(" (real)", " real") for n in names]

# ---- Figure 1: rebased indices and drawdowns
fig, axes = plt.subplots(2, 1, figsize=(8.0, 6.0), sharex=True, gridspec_kw={"height_ratios": [2, 1.2]})
ax = axes[0]
for c, col, lab in [("EGX30", RED, "EGX 30 (EGP)"), ("TASI", PETROL, "TASI (SAR)"), ("SPX", NAVY, "S&P 500 (USD)"), ("STOXX", GREY, "Euro Stoxx 50 (EUR)")]:
    s = px[c] / px[c].iloc[0]; ax.plot(s.index, s, color=col, lw=1.3, label=lab)
e = px["EGPUSD"] / px["EGPUSD"].iloc[0]; ax.plot(e.index, e, color=GOLD, lw=1.2, ls="--", label="EGP per USD (rebased)")
ax.set_yscale("log"); ax.set_ylabel("Index level, Jan 2010 = 1 (log)"); ax.legend(frameon=False, ncol=2, loc="upper left")
for d, l in [("2016-11-03", "Nov 2016 float"), ("2020-03-16", "COVID"), ("2022-03-21", "Mar 2022"), ("2024-03-06", "Mar 2024 float")]:
    ax.axvline(pd.Timestamp(d), color=GREY, lw=.7, ls=":"); ax.text(pd.Timestamp(d), ax.get_ylim()[1] * 0.92, l, fontsize=8.5, rotation=90, va="top", ha="right", color=GREY)
ax2 = axes[1]
for c, col in [("EGX30", RED), ("TASI", PETROL), ("SPX", NAVY)]:
    dd = px[c] / px[c].cummax() - 1; ax2.fill_between(dd.index, dd * 100, 0, color=col, alpha=.25); ax2.plot(dd.index, dd * 100, color=col, lw=.9)
ax2.set_ylabel("Drawdown from peak (%)"); ax2.set_ylim(-70, 2)
plt.tight_layout(); plt.savefig(f"{OUT}/fig1_indices.png", dpi=300, bbox_inches="tight"); plt.close()

# ---- Figure 2: one-year 99.5 % VaR/ES by method with the simplified standard-formula charge
meth = [("G", "Gaussian"), ("H", "Historical"), ("B", "Block bootstrap"), ("T", "t-copula")]; cols = [GREY, GOLD, PETROL, NAVY]
fig, ax = plt.subplots(figsize=(8.2, 4.0)); x = np.arange(len(names)); wd = 0.19
for i, (k, lab) in enumerate(meth):
    v = [R["ports"][n][f"{k}_VaR_0.995"] * 100 for n in names]; es = [R["ports"][n][f"{k}_ES_0.995"] * 100 for n in names]
    ax.bar(x + (i - 1.5) * wd, v, wd, color=cols[i], label=f"{lab} VaR")
    ax.bar(x + (i - 1.5) * wd, [a - b for a, b in zip(es, v)], wd, bottom=v, color=cols[i], alpha=.4, hatch="//", label="ES increment" if i == 0 else None)
sf = [(R["ports"][n]["SF_SCR"] if n != "Egypt insurer (real)" else R["ports"]["Egypt insurer"]["SF_SCR"]) * 100 for n in names]
ax.scatter(x, sf, marker="D", color=RED, zorder=5, s=36, label="Simplified standard-formula market charge")
ax.axhline(0, color="k", lw=.6); ax.set_xticks(x); ax.set_xticklabels(short); ax.set_ylabel("One-year loss at 99.5% (% of portfolio)")
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.13)); ax.set_ylim(-2, 27)
plt.tight_layout(); plt.savefig(f"{OUT}/fig2_methods.png", dpi=300, bbox_inches="tight"); plt.close()

# ---- Figure 3: bootstrapped loss distributions (regenerated with the same generator, 20,000 paths) for four portfolios
def stationary_bootstrap(x, rng, n_paths=20000, horizon=250, mean_block=60):
    p = 1 / mean_block; n = len(x); starts = rng.integers(0, n, size=(n_paths, horizon)); restart = rng.random((n_paths, horizon)) < p; restart[:, 0] = True
    idx = np.empty((n_paths, horizon), dtype=int); idx[:, 0] = starts[:, 0]
    for t in range(1, horizon): idx[:, t] = np.where(restart[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
    return 1 - np.exp(x[idx].sum(axis=1))
fig, axes = plt.subplots(1, 4, figsize=(9.0, 3.1))
for ax, (name, col) in zip(axes, [("EEA representative", NAVY), ("Egypt insurer", RED), ("Egypt insurer (real)", GOLD), ("Saudi insurer", PETROL)]):
    cols_ = list(PORTS[name].keys()); a0, a1 = WIN[name]; X = r.loc[a0:a1, cols_].dropna(); xx = X.values @ np.array([PORTS[name][c] for c in cols_])
    b = stationary_bootstrap(xx, np.random.default_rng(2026)) * 100; p = R["ports"][name]; dz = R["review"]["drift"][name]["gauss_zero"]["VaR"] * 100
    ax.hist(b, bins=120, density=True, color=col, alpha=.45)
    for v, ls, lw in [(p["G_VaR_0.995"] * 100, ":", 1.2), (dz, "-.", 1.0), (p["B_VaR_0.995"] * 100, "--", 1.2), (p["B_ES_0.995"] * 100, "-", 1.4)]:
        ax.axvline(v, color="k", ls=ls, lw=lw)
    ax.set_title(name.replace(" insurer", "").replace(" representative", ""), fontsize=10.5); ax.set_xlabel("One-year loss (%)")
    ax.set_xlim(np.quantile(b, .0005) - 2, max(p["B_ES_0.995"] * 100 + 4, np.quantile(b, .9995)))
axes[0].set_ylabel("Density")
axes[3].legend(handles=[Line2D([0], [0], color="k", ls=":", label="Gaussian VaR (with drift)"), Line2D([0], [0], color="k", ls="-.", label="Gaussian VaR (zero drift)"),
                        Line2D([0], [0], color="k", ls="--", label="Bootstrap VaR"), Line2D([0], [0], color="k", ls="-", label="Bootstrap ES")], fontsize=7.5, frameon=False, loc="upper left")
plt.tight_layout(); plt.savefig(f"{OUT}/fig3_lossdist.png", dpi=300, bbox_inches="tight"); plt.close()

# ---- Figure 4: diversification benefit, full sample and stress windows
S = R["stress"]; wins = list(next(iter(S.values())).keys()); labs = {"full": "Full sample", "GFC aftermath 2010-11": "2010–11", "COVID 2020": "COVID 2020", "Rates shock 2022": "Rates 2022", "Egypt float 2016-17": "Egypt float 2016–17", "Egypt 2022-24 devaluations": "Egypt 2022–24"}
fig, ax = plt.subplots(figsize=(8.2, 3.4)); x = np.arange(len(names)); wd = 0.8 / len(wins)
for i, wn in enumerate(wins):
    ax.bar(x + (i - len(wins) / 2 + .5) * wd, [(S[n][wn][0] if S[n][wn][0] == S[n][wn][0] else 0) * 100 for n in names], wd, label=labs.get(wn, wn), color=[NAVY, GREY, GOLD, PETROL, RED, BLUE2][i % 6])
ax.set_xticks(x); ax.set_xticklabels(short); ax.set_ylabel("Diversification benefit (%)"); ax.legend(frameon=False, ncol=3); ax.axhline(0, color="k", lw=.6)
plt.tight_layout(); plt.savefig(f"{OUT}/fig4_divers.png", dpi=300, bbox_inches="tight"); plt.close()

# ---- Figure 5: daily 99 % VaR exceedances by model, static and volatility-tracking
BT, BD = R["backtest"], R["review"]["backtest_dyn"]; bn = ["Balanced (US)", "EEA representative", "Egypt insurer", "Saudi insurer"]
models = [("gauss", "Gaussian", GREY, BT), ("t", "Student-t", BLUE2, BT), ("hist", "Historical", GOLD, BT), ("ewma_gauss", "EWMA-Gaussian", "#9AA3AB", BD), ("ewma_t", "EWMA-t", PETROL, BD), ("fhs", "Filtered HS", NAVY, BD)]
fig, ax = plt.subplots(figsize=(8.2, 3.6)); x = np.arange(len(bn)); wd = 0.13
for i, (k, lab, col, src) in enumerate(models):
    ax.bar(x + (i - 2.5) * wd, [src[n][k]["exceedances"] / src[n][k]["expected"] for n in bn], wd, color=col, label=lab)
ax.axhline(1, color=RED, lw=1.2, ls="--", label="Expected (1 % of days)")
ax.set_xticks(x); ax.set_xticklabels([n.replace(" (US)", " US").replace(" representative", "").replace(" insurer", "") for n in bn]); ax.set_ylabel("Exceedances ÷ expected")
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.13)); ax.set_ylim(0, 3)
plt.tight_layout(); plt.savefig(f"{OUT}/fig5_backtests.png", dpi=300, bbox_inches="tight"); plt.close()
print("figures saved to", OUT)
