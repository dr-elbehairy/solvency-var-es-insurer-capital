"""
v4 reviewer checks (added October 2026). Reads data/daily_returns.csv, data/weights.csv, ports.json and sol_results.json,
and writes the results under sol_results.json["review"]. Every number quoted in Section 4.2 of the paper comes from here.

Checks:
  S1  drift convention: zero-drift Gaussian VaR/ES and demeaned historical / block-bootstrap distributions (99.5 %)
  S2  Monte-Carlo and sampling error: 100,000-path bootstrap with batch standard errors, block length 20/60/120,
      three seeds, and a block-bootstrap interval for the overlapping-window historical 99.5 % quantile
  S3  volatility-tracking models in the daily backtest: EWMA-Gaussian, EWMA-Student-t and EWMA-filtered historical
      simulation (RiskMetrics lambda = 0.94), with Kupiec, Christoffersen and Acerbi-Szekely Z2
  S4  degrees of freedom: Student-t fits on daily and monthly returns of every series; copula df per portfolio
"""
import os, json, numpy as np, pandas as pd
from scipy import stats
HERE = os.path.dirname(os.path.abspath(__file__))
r = pd.read_csv(f"{HERE}/data/daily_returns.csv", index_col=0, parse_dates=True)
W = pd.read_csv(f"{HERE}/data/weights.csv", index_col=0)
PJ = json.load(open(f"{HERE}/ports.json")); PORTS, WIN = PJ["PORTS"], PJ["WINDOW"]
R = json.load(open(f"{HERE}/sol_results.json"))
A = 0.995
names = list(PORTS.keys())

def port_series(name):
    cols = list(PORTS[name].keys()); a0, a1 = WIN[name]
    X = r.loc[a0:a1, cols].dropna(); w = np.array([PORTS[name][c] for c in cols])
    return X, w, X.values @ w

def var_es(l, a=A):
    v = np.quantile(l, a); return float(v), float(l[l >= v].mean())

def stationary_bootstrap(x, rng, n_paths=20000, horizon=250, mean_block=60):
    p = 1 / mean_block; n = len(x)
    starts = rng.integers(0, n, size=(n_paths, horizon)); restart = rng.random((n_paths, horizon)) < p; restart[:, 0] = True
    idx = np.empty((n_paths, horizon), dtype=int); idx[:, 0] = starts[:, 0]
    for t in range(1, horizon): idx[:, t] = np.where(restart[:, t], starts[:, t], (idx[:, t - 1] + 1) % n)
    return 1 - np.exp(x[idx].sum(axis=1))

review = {"drift": {}, "mc": {}, "hist_ci": {}, "df": {}, "backtest_dyn": {}}

# ---------------------------------------------------------------- S1 drift convention
for n in names:
    X, w, x = port_series(n)
    mu_d, cov_d = X.mean().values, X.cov().values
    sig = np.sqrt(250 * w @ cov_d @ w); mu = 250 * w @ mu_d; z = stats.norm.ppf(A)
    g0 = {"VaR": float(sig * z), "ES": float(sig * stats.norm.pdf(z) / (1 - A))}
    gmu = {"VaR": float(sig * z - mu), "ES": float(sig * stats.norm.pdf(z) / (1 - A) - mu)}
    xd = x - x.mean()
    hl = 1 - np.exp(pd.Series(xd).rolling(250).sum().dropna().values); hv, he = var_es(hl)
    rng = np.random.default_rng(2026); bl = stationary_bootstrap(xd, rng); bv, be = var_es(bl)
    review["drift"][n] = {"mu_ann": float(mu), "sig_ann": float(sig), "gauss_mu": gmu, "gauss_zero": g0,
                          "hist_demeaned": {"VaR": hv, "ES": he}, "boot_demeaned": {"VaR": bv, "ES": be}}
    print(f"S1 {n:22s} mu={100*mu:5.1f} G(mu) {100*gmu['VaR']:5.1f}/{100*gmu['ES']:5.1f}  G(0) {100*g0['VaR']:5.1f}/{100*g0['ES']:5.1f}  H0 {100*hv:5.1f}/{100*he:5.1f}  B0 {100*bv:5.1f}/{100*be:5.1f}")

# ---------------------------------------------------------------- S2 Monte-Carlo and sampling error
for n in names:
    X, w, x = port_series(n); out = {}
    # 100,000 paths, batch standard errors (10 batches of 10,000)
    rng = np.random.default_rng(2026); bl = stationary_bootstrap(x, rng, n_paths=100000)
    v, e = var_es(bl); bv = []; bes = []
    for b in range(10):
        vb, eb = var_es(bl[b * 10000:(b + 1) * 10000]); bv.append(vb); bes.append(eb)
    out["paths100k"] = {"VaR": v, "ES": e, "se_VaR_10k": float(np.std(bv, ddof=1)), "se_ES_10k": float(np.std(bes, ddof=1)),
                        "se_VaR_100k": float(np.std(bv, ddof=1) / np.sqrt(10)), "se_ES_100k": float(np.std(bes, ddof=1) / np.sqrt(10))}
    # block length
    out["block"] = {}
    for mb in (20, 60, 120):
        rng = np.random.default_rng(2026); bl = stationary_bootstrap(x, rng, mean_block=mb); vv, ee = var_es(bl); out["block"][str(mb)] = {"VaR": vv, "ES": ee}
    # seeds
    out["seeds"] = {}
    for s in (2026, 7, 99):
        rng = np.random.default_rng(s); bl = stationary_bootstrap(x, rng); vv, ee = var_es(bl); out["seeds"][str(s)] = {"VaR": vv, "ES": ee}
    review["mc"][n] = out
    print(f"S2 {n:22s} 100k {100*v:5.1f}/{100*e:5.1f} seES={100*out['paths100k']['se_ES_100k']:.2f}  blocks " +
          " ".join(f"{k}:{100*d['VaR']:4.1f}/{100*d['ES']:4.1f}" for k, d in out["block"].items()) + "  seeds " + " ".join(f"{100*d['ES']:4.1f}" for d in out["seeds"].values()))

# historical overlapping-window 99.5 % quantile: block-bootstrap (mean block 60) of the daily series, 300 replications
for n in names:
    X, w, x = port_series(n); rng = np.random.default_rng(2026); n_ = len(x); q = []
    for b in range(300):
        p = 1 / 60; starts = rng.integers(0, n_, size=n_); restart = rng.random(n_) < p; restart[0] = True
        idx = np.empty(n_, dtype=int); idx[0] = starts[0]
        for t in range(1, n_): idx[t] = starts[t] if restart[t] else (idx[t - 1] + 1) % n_
        xs = x[idx]; hl = 1 - np.exp(pd.Series(xs).rolling(250).sum().dropna().values); q.append(np.quantile(hl, A))
    q = np.array(q); hl0 = 1 - np.exp(pd.Series(x).rolling(250).sum().dropna().values)
    review["hist_ci"][n] = {"point": float(np.quantile(hl0, A)), "lo": float(np.quantile(q, 0.025)), "hi": float(np.quantile(q, 0.975)),
                            "n_windows": int(len(hl0)), "indep_years": float(len(hl0) / 250)}
    print(f"S2h {n:22s} hist 99.5 {100*review['hist_ci'][n]['point']:5.1f}  CI {100*review['hist_ci'][n]['lo']:5.1f}–{100*review['hist_ci'][n]['hi']:5.1f}")

# ---------------------------------------------------------------- S4 degrees of freedom
daily_df = {}; monthly_df = {}
for c in [c for c in r.columns if not c.endswith("_R")]:
    s = r[c].dropna().loc["2010-01-05":]
    if c in ("EGDEP", "SACASH", "TBILL", "EUCASH", "USD_EGP", "SPX_EGP"): continue  # accrual / step series: t fit not meaningful
    z = (s - s.mean()) / s.std(); daily_df[c] = float(stats.t.fit(z)[0])
    m = s.resample("M").sum(); zm = (m - m.mean()) / m.std(); monthly_df[c] = float(stats.t.fit(zm)[0])
review["df"] = {"daily": daily_df, "monthly": monthly_df, "copula": {n: R["ports"][n].get("t_df_copula") for n in names}}
print("S4 daily df:", {k: round(v, 1) for k, v in daily_df.items()}); print("S4 monthly df:", {k: round(v, 1) for k, v in monthly_df.items()}); print("S4 copula df:", review["df"]["copula"])

# ---------------------------------------------------------------- S3 volatility-tracking backtests
DF_GRID = np.array([3, 3.5, 4, 4.5, 5, 6, 7, 8, 10, 12, 15, 20, 30, 50])
def tests(exc, es_ratio, T, a_v=0.99, a_e=0.975):
    N1 = int(exc.sum()); p = 1 - a_v; ph = N1 / T
    lr = -2 * ((T - N1) * np.log(1 - p) + N1 * np.log(p) - (T - N1) * np.log(1 - ph) - N1 * np.log(ph)) if 0 < N1 < T else np.nan
    n00 = n01 = n10 = n11 = 0
    for a_, b_ in zip(exc[:-1], exc[1:]):
        if a_ == 0 and b_ == 0: n00 += 1
        elif a_ == 0 and b_ == 1: n01 += 1
        elif a_ == 1 and b_ == 0: n10 += 1
        else: n11 += 1
    p01 = n01 / (n00 + n01) if n00 + n01 else 0; p11 = n11 / (n10 + n11) if n10 + n11 else 0; p1 = (n01 + n11) / (T - 1)
    def ll(pa, pb):
        v = 0.0
        if n00: v += n00 * np.log(1 - pa)
        if n01: v += n01 * np.log(pa)
        if n10: v += n10 * np.log(1 - pb)
        if n11 and pb > 0: v += n11 * np.log(pb)
        return v
    lri = -2 * (ll(p1, p1) - ll(p01, p11)) if 0 < p01 < 1 else np.nan
    z2 = float(es_ratio.sum() / (T * (1 - a_e)) - 1)
    return dict(T=int(T), exceedances=N1, expected=float(T * p), rate=float(ph),
                kupiec_p=float(1 - stats.chi2.cdf(lr, 1)) if lr == lr else None,
                christoffersen_p=float(1 - stats.chi2.cdf(lri, 1)) if lri == lri else None, AS_Z2=z2)

def backtest_dyn(x, a_v=0.99, a_e=0.975, win=500, lam=0.94):
    n = len(x); T = n - win
    # EWMA variance recursion over the whole series, initialised on the first window
    s2 = np.empty(n); s2[:win] = np.var(x[:win]);
    for t in range(win, n): s2[t] = lam * s2[t - 1] + (1 - lam) * x[t - 1] ** 2
    sig = np.sqrt(s2)
    rec = {k: {"exc": np.zeros(T, int), "es": np.zeros(T)} for k in ("ewma_gauss", "ewma_t", "fhs")}
    zv, ze = stats.norm.ppf(a_v), stats.norm.ppf(a_e); dfs = []
    for j, i in enumerate(range(win, n)):
        L = -x[i]; s = sig[i]
        # EWMA-Gaussian (zero conditional mean)
        vG, vGe, eG = s * zv, s * ze, s * stats.norm.pdf(ze) / (1 - a_e)
        # EWMA-t: df fitted by profile likelihood on the window's EWMA-standardised residuals, variance-matched
        z = x[i - win:i] / sig[i - win:i]
        if j % 20 == 0:   # refit df every 20 days to keep runtime modest
            best = None
            for dfc in DF_GRID:
                cc = np.sqrt((dfc - 2) / dfc); ll_ = stats.t.logpdf(z, dfc, 0, cc).sum()
                if best is None or ll_ > best[0]: best = (ll_, dfc, cc)
            _, df_, c = best
        dfs.append(df_); qv, qe = stats.t.ppf(a_v, df_), stats.t.ppf(a_e, df_)
        vT, vTe = s * c * qv, s * c * qe; eT = s * c * (stats.t.pdf(qe, df_) * (df_ + qe ** 2) / ((df_ - 1) * (1 - a_e)))
        # filtered historical simulation: empirical quantiles of standardised residuals scaled by current volatility
        zl = -z; vH = s * np.quantile(zl, a_v); vHe = s * np.quantile(zl, a_e); eH = s * zl[zl >= np.quantile(zl, a_e)].mean()
        for k, v, ve, e in (("ewma_gauss", vG, vGe, eG), ("ewma_t", vT, vTe, eT), ("fhs", vH, vHe, eH)):
            rec[k]["exc"][j] = int(L > v); rec[k]["es"][j] = (L / e) * int(L > ve) if e > 0 else 0.0
    out = {k: tests(rec[k]["exc"], rec[k]["es"], T) for k in rec}
    out["t_df_median"] = float(np.median(dfs)); out["t_df_min"] = float(np.min(dfs)); out["t_df_max"] = float(np.max(dfs))
    return out

for n in ["Balanced (US)", "EEA representative", "Egypt insurer", "Egypt insurer (real)", "Saudi insurer"]:
    X, w, x = port_series(n); review["backtest_dyn"][n] = backtest_dyn(x)
    print("S3", n, {k: (v["exceedances"], round(v["AS_Z2"], 2), round(v["kupiec_p"], 3) if v["kupiec_p"] is not None else None, round(v["christoffersen_p"], 3) if v["christoffersen_p"] is not None else None) for k, v in review["backtest_dyn"][n].items() if isinstance(v, dict)})

# Egyptian real-return years (text check)
real = R["egypt_real"]; review["egypt_positive_real_years"] = [int(y) for y in sorted(real) if real[y]["real"] > 0]
R["review"] = review
json.dump(R, open(f"{HERE}/sol_results.json", "w"), indent=2, default=float)
print("review saved; positive real years:", review["egypt_positive_real_years"])
