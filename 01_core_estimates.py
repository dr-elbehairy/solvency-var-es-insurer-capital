"""Step 01: builds the aligned daily return panel, the six portfolios and the one-year VaR/ES estimates (Tables 1-3), the simplified standard-formula comparator, stress-window diversification and the Egyptian real-return table. Writes sol_results.json, ports.json and data/daily_returns.csv."""
"""
v3 data build: every series is an observed market or official series (no assumed parameters, no cross-market proxies).
Mature (US) set: SPX, VNQ, LQD, IEF, BIL.   EEA set: Euro Stoxx 50, iShares Core EUR Govt (EUNH.DE), iShares Core EUR Corp (IEAC.MI),
iShares European Property (IQQP.DE), iShares eb.rexx Money Market (EXVM.DE).
Egypt: EGX 30; equal-weight listed developer basket (TMGH, PHDC, ORHD, HELI); bank deposits accrued at the CBE overnight deposit rate
(decision dates 2005-2026); USD deposit = EGP/USD + BIL; foreign equity = SPX in EGP; real terms deflated by monthly CPI (WB GEM).
Saudi: TASI; equal-weight listed REIT basket (12 Tadawul REITs); SP Funds Dow Jones Global Sukuk ETF (SPSK); cash accrued at monthly
3M SAIBOR (SAMA via KAPSARC). Saudi window starts 2020-01-02 (first full month of SPSK); all others start 2010-01-05.
"""
import numpy as np, pandas as pd, json, warnings
from scipy import stats
warnings.filterwarnings("ignore")
rng = np.random.default_rng(2026)
import os
HERE = os.path.dirname(os.path.abspath(__file__)); H = os.path.join(HERE, "data")   # raw inputs and derived files live in data/
END = "2026-09-24"
def rd(f, col=None):
    d = pd.read_csv(f"{H}/{f}", index_col=0, parse_dates=True); d.index = d.index.normalize(); return d if col is None else d[col]
g = rd("global_daily.csv"); eu = rd("euro_saudi_daily.csv"); egx = rd("egx30_tv_daily.csv", "close"); tasi = rd("tasi_tv_daily.csv", "close")
tmgh = rd("egx_tmgh_tv_daily.csv", "close"); egre = rd("egx_realestate_tv.csv"); fx = rd("fx_daily.csv"); reits = rd("saudi_reits_daily.csv")
# ---- step series: CBE overnight deposit rate (daily accrual), SAIBOR 3M monthly (daily accrual), monthly CPI (daily accrual)
pol = pd.read_csv(f"{H}/egypt_policy_rate.csv", parse_dates=["date"]).set_index("date")["deposit_rate"] / 100
sai = pd.read_csv(f"{H}/saibor3m_monthly.csv", parse_dates=["date"]).set_index("date")["interest_rate"] / 100
def cpi_monthly(iso):
    try:
        c = pd.read_csv(f"{H}/gem_cpi_m_{iso}.csv"); c["date"] = pd.to_datetime(c.period.str.replace("M", "-") + "-01"); c = c.set_index("date")["cpi"].sort_index()
        if len(c) > 100: return c
    except Exception: pass
    return None
cpi_eg = cpi_monthly("EGY")
def daily_from_steps(series, index, per_year=250):
    s = series.sort_index().reindex(series.index.union(index)).ffill().reindex(index); return np.log(1 + s) / per_year
# ---- price panel
px = pd.DataFrame({"SPX": g.SPX, "STOXX": g.STOXX, "REIT": g.REIT, "IGCORP": g.IGCORP, "UST": g.UST7_10, "TBILL": g.TBILL,
                   "EUGOV": eu.EUGOV, "EUCORP": eu.EUCORP, "EUPROP": eu.EUPROP, "EUCASH": eu.EUCASH,
                   "EGX30": egx, "TASI": tasi, "EGPUSD": fx.EGPUSD, "SUKUK": eu.SUKUK_ETF})
dev = pd.concat([tmgh.rename("TMGH"), egre[["PHDC", "ORHD", "HELI"]]], axis=1).loc["2009-12-01":END].ffill()
px["EGDEV"] = np.exp(np.log(dev / dev.iloc[0]).mean(axis=1))          # equal-weight developer basket, rebalanced daily
rb = reits.loc["2018-08-06":END].ffill(); rb = rb.dropna(axis=1, thresh=int(0.9 * len(rb)))
px["SAREIT"] = np.exp(np.log(rb / rb.iloc[0]).mean(axis=1))
px = px.loc["2009-12-01":END].ffill()
r_all = np.log(px / px.shift(1))
idx = r_all.index
r_all["EGDEP"] = daily_from_steps(pol, idx)                            # CBE overnight deposit rate accrual
r_all["SACASH"] = daily_from_steps(sai, idx)                           # SAIBOR 3M accrual
r_all["USD_EGP"] = r_all["TBILL"] + r_all["EGPUSD"]
r_all["SPX_EGP"] = r_all["SPX"] + r_all["EGPUSD"]
if cpi_eg is not None:
    infl_m = np.log(cpi_eg / cpi_eg.shift(12)).dropna()                # trailing 12-month inflation, monthly
    infl = infl_m.reindex(infl_m.index.union(idx)).ffill().reindex(idx) / 250
    CPI_SOURCE = "World Bank Global Economic Monitor, monthly CPI"
else:
    wb = pd.read_csv(f"{H}/wb_rates.csv"); cpi_a = wb[(wb.iso == "EGY") & (wb.ind == "FP.CPI.TOTL.ZG")].set_index("year")["value"] / 100
    infl = pd.Series([np.log(1 + cpi_a.get(d.year, cpi_a.iloc[-1])) / 250 for d in idx], index=idx); CPI_SOURCE = "World Development Indicators, annual CPI"
for c in ["EGX30", "EGDEV", "EGDEP", "USD_EGP", "SPX_EGP"]: r_all[c + "_R"] = r_all[c] - infl
r_all = r_all.drop(columns=["EGPUSD"])

PORTS = {
 "Conservative (US)": {"SPX": 0.10, "REIT": 0.05, "IGCORP": 0.20, "UST": 0.55, "TBILL": 0.10},
 "Balanced (US)":     {"SPX": 0.25, "REIT": 0.10, "IGCORP": 0.20, "UST": 0.40, "TBILL": 0.05},
 "Growth (US)":       {"SPX": 0.45, "REIT": 0.15, "IGCORP": 0.15, "UST": 0.20, "TBILL": 0.05},
 "EEA representative": {"STOXX": 0.22, "EUPROP": 0.04, "EUCORP": 0.36, "EUGOV": 0.27, "EUCASH": 0.11},
 "Egypt insurer":      {"EGX30": 0.15, "EGDEV": 0.05, "EGDEP": 0.70, "USD_EGP": 0.05, "SPX_EGP": 0.05},
 "Egypt insurer (real)": {"EGX30_R": 0.15, "EGDEV_R": 0.05, "EGDEP_R": 0.70, "USD_EGP_R": 0.05, "SPX_EGP_R": 0.05},
 "Saudi insurer":      {"TASI": 0.20, "SAREIT": 0.05, "SUKUK": 0.30, "SACASH": 0.45},
}
WINDOW = {n: ("2010-01-05", END) for n in PORTS}; WINDOW["Saudi insurer"] = ("2020-01-02", END)

def var_es(losses, a):
    v = np.quantile(losses, a); return float(v), float(losses[losses >= v].mean())
def gaussian(mu_d, cov_d, w, a):
    mu = 250 * w @ mu_d; sig = np.sqrt(250 * w @ cov_d @ w); z = stats.norm.ppf(a)
    return float(sig * z - mu), float(sig * stats.norm.pdf(z) / (1 - a) - mu)
def stationary_bootstrap(x, n_paths=20000, horizon=250, p=1/60):
    n = len(x); starts = rng.integers(0, n, size=(n_paths, horizon)); restart = rng.random((n_paths, horizon)) < p; restart[:, 0] = True
    idx_ = np.empty((n_paths, horizon), dtype=int); idx_[:, 0] = starts[:, 0]
    for t in range(1, horizon): idx_[:, t] = np.where(restart[:, t], starts[:, t], (idx_[:, t - 1] + 1) % n)
    return 1 - np.exp(x[idx_].sum(axis=1))
def t_copula_monthly(Rm, w, n_sims=100000):
    X = Rm.values; k = X.shape[1]; cols = list(Rm.columns)
    emp = [j for j, c in enumerate(cols) if c.startswith(("EGDEP", "USD_EGP", "TBILL", "SPX_EGP", "SACASH", "EUCASH"))]
    params = [None if j in emp else stats.t.fit(X[:, j]) for j in range(k)]
    pr = X @ w; nu_c = max(2.5, min(stats.t.fit(pr)[0], 30.0)); C = np.corrcoef(X.T); L = np.linalg.cholesky(C + 1e-9 * np.eye(k)); tot = np.zeros(n_sims)
    for m in range(12):
        Z = rng.standard_normal((n_sims, k)) @ L.T; chi = rng.chisquare(nu_c, n_sims) / nu_c; U = stats.t.cdf(Z / np.sqrt(chi)[:, None], nu_c)
        tot += np.column_stack([np.quantile(X[:, j], U[:, j]) if params[j] is None else stats.t.ppf(U[:, j], *params[j]) for j in range(k)]) @ w
    return 1 - np.exp(tot), float(nu_c)

res = {"period_main": "2010-01-05..2026-09-24", "period_saudi": "2020-01-02..2026-09-24", "cpi_source": CPI_SOURCE, "ports": {}, "windows": WINDOW}
A = [0.95, 0.99, 0.995]
for name, wdict in PORTS.items():
    a0, a1 = WINDOW[name]; cols = list(wdict.keys()); R = r_all.loc[a0:a1, cols].dropna(); w = np.array([wdict[c] for c in cols])
    mu_d, cov_d = R.mean().values, R.cov().values; out = {"N": int(len(R)), "start": str(R.index.min().date()), "end": str(R.index.max().date())}
    out["mu_ann"], out["sig_ann"] = float(250 * w @ mu_d), float(np.sqrt(250 * w @ cov_d @ w))
    out["div_benefit"] = float(1 - out["sig_ann"] / (w @ np.sqrt(250 * np.diag(cov_d))))
    for a in A: out[f"G_VaR_{a}"], out[f"G_ES_{a}"] = gaussian(mu_d, cov_d, w, a)
    x = R.values @ w; hl = 1 - np.exp(pd.Series(x).rolling(250).sum().dropna().values)
    for a in A: out[f"H_VaR_{a}"], out[f"H_ES_{a}"] = var_es(hl, a)
    bl = stationary_bootstrap(x)
    for a in A: out[f"B_VaR_{a}"], out[f"B_ES_{a}"] = var_es(bl, a)
    Rm = R.resample("M").sum(); tl, nu = t_copula_monthly(Rm, w)
    for a in A: out[f"T_VaR_{a}"], out[f"T_ES_{a}"] = var_es(tl, a)
    out["t_df_copula"] = nu; out["N_monthly"] = int(len(Rm)); out["worst_year_hist"] = float(hl.max()); out["skew_daily"] = float(stats.skew(x)); out["kurt_daily"] = float(stats.kurtosis(x))
    np.save(f"{H}/boot_{name.replace(' ', '_').replace('(', '').replace(')', '')}.npy", bl); res["ports"][name] = out
    print(f"{name:22s} N={len(R)} mu={out['mu_ann']*100:5.1f} sig={out['sig_ann']*100:5.1f} 99.5: G {out['G_VaR_0.995']*100:5.1f}/{out['G_ES_0.995']*100:5.1f} H {out['H_VaR_0.995']*100:5.1f}/{out['H_ES_0.995']*100:5.1f} B {out['B_VaR_0.995']*100:5.1f}/{out['B_ES_0.995']*100:5.1f} T {out['T_VaR_0.995']*100:5.1f}/{out['T_ES_0.995']*100:5.1f}")

# ---- standard-formula comparator (Delegated Regulation 2015/35): equity 39%/49%, property 25%, IR up 168bp on duration, spread 1.4%/yr dur, FX 25%
DUR = {"IGCORP": 8.5, "UST": 7.5, "EUGOV": 7.0, "EUCORP": 5.0, "SUKUK": 4.5}   # published effective durations of the funds (approx., Sept 2026 factsheets)
def sf_scr(w, emerging):
    eq = 0.49 if emerging else 0.39
    L_eq = eq * sum(w.get(k, 0) for k in ["SPX", "STOXX", "EGX30", "TASI", "SPX_EGP"])
    L_prop = 0.25 * sum(w.get(k, 0) for k in ["REIT", "EUPROP", "EGDEV", "SAREIT"])
    L_ir = sum(w.get(k, 0) * DUR[k] * 0.0168 for k in ["UST", "EUGOV"]) + w.get("SUKUK", 0) * 0.5 * DUR["SUKUK"] * 0.0168
    L_sp = sum(w.get(k, 0) * min(DUR[k] * 0.014, 0.35) for k in ["IGCORP", "EUCORP"]) + w.get("SUKUK", 0) * 0.5 * min(DUR["SUKUK"] * 0.014, 0.35)
    L_fx = 0.25 * (w.get("USD_EGP", 0) + w.get("SPX_EGP", 0))
    v = np.array([L_ir, L_eq, L_prop, L_sp, L_fx]); C = np.array([[1, 0, 0, 0, .25], [0, 1, .75, .75, .25], [0, .75, 1, .5, .25], [0, .75, .5, 1, .25], [.25, .25, .25, .25, 1]])
    return float(np.sqrt(v @ C @ v)), dict(interest=float(L_ir), equity=float(L_eq), property=float(L_prop), spread=float(L_sp), currency=float(L_fx))
for name, wdict in PORTS.items():
    wn = {k.replace("_R", ""): v for k, v in wdict.items()}; scr, parts = sf_scr(wn, name.startswith(("Egypt", "Saudi")))
    res["ports"][name]["SF_SCR"] = scr; res["ports"][name]["SF_parts"] = parts; res["ports"][name]["SaudiRBC_equity50"] = float(0.5 * sum(wn.get(k, 0) for k in ["SPX", "STOXX", "EGX30", "TASI", "SPX_EGP"]))
    print(f"SF {name:22s} {scr*100:5.1f}")
# ---- stress windows
SW = {"GFC aftermath 2010-11": ("2010-01-01", "2011-12-31"), "COVID 2020": ("2020-02-15", "2020-06-30"), "Rates shock 2022": ("2022-01-01", "2022-10-31"),
      "Egypt float 2016-17": ("2016-11-01", "2017-06-30"), "Egypt 2022-24 devaluations": ("2022-03-01", "2024-06-30")}
def divb(R, w):
    c = R.cov().values * 250; sig = np.sqrt(w @ c @ w); return float(1 - sig / (w @ np.sqrt(np.diag(c)))), float(sig)
res["stress"] = {}
for name, wdict in PORTS.items():
    cols = list(wdict.keys()); w = np.array([wdict[c] for c in cols]); a0, a1 = WINDOW[name]; R = r_all.loc[a0:a1, cols].dropna(); d = {"full": divb(R, w)}
    for k, (a, b) in SW.items():
        Rw = R.loc[a:b]; d[k] = divb(Rw, w) if len(Rw) > 40 else (float("nan"), float("nan"))
    res["stress"][name] = d
# ---- asset moments (each on its own available window)
res["asset_moments"] = {}
for c in [c for c in r_all.columns if not c.endswith("_R")]:
    s = r_all[c].dropna(); s = s.loc["2010-01-05":]; wy = 1 - np.exp(s.rolling(250).sum().min()) if len(s) > 300 else float("nan")
    res["asset_moments"][c] = dict(start=str(s.index.min().date()), n=int(len(s)), mu=float(250 * s.mean()), sig=float(np.sqrt(250) * s.std()), skew=float(stats.skew(s)), kurt=float(stats.kurtosis(s)), worst_day=float(s.min()), worst_year=float(wy))
# ---- Egypt nominal vs real annual table
pol_d = pol.reindex(pol.index.union(idx)).ffill().reindex(idx)
yrs = range(2015, 2026); eg_tab = {}
for y in yrs:
    dep_y = float(pol_d.loc[str(y)].mean()) if len(pol_d.loc[str(y)]) else float("nan")
    inf_y = float(np.exp(infl.loc[str(y)].sum() * 250 / max(len(infl.loc[str(y)]), 1)) - 1) if len(infl.loc[str(y)]) else float("nan")
    eg_tab[y] = dict(deposit=dep_y, cpi=inf_y, real=dep_y - inf_y)
res["egypt_real"] = {str(k): v for k, v in eg_tab.items()}
res["egx_annual"] = {str(k.year): float(v) for k, v in px["EGX30"].resample("A").last().pct_change().dropna().items()}
res["tasi_annual"] = {str(k.year): float(v) for k, v in px["TASI"].resample("A").last().pct_change().dropna().items()}
res["egp_annual_depr"] = {str(k.year): float(v) for k, v in px["EGPUSD"].resample("A").last().pct_change().dropna().items()}
json.dump(res, open(f"{HERE}/sol_results.json", "w"), indent=2, default=float)
r_all.to_csv(f"{H}/daily_returns.csv"); px.to_csv(f"{H}/prices_aligned.csv")
pd.DataFrame({n: pd.Series(w) for n, w in PORTS.items()}).T.fillna(0).to_csv(f"{H}/weights.csv")
json.dump({"PORTS": PORTS, "WINDOW": WINDOW}, open(f"{HERE}/ports.json", "w"), indent=2)
print("core saved")
