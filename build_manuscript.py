# -*- coding: utf-8 -*-
"""Solvency II VaR vs ES paper, v4 final (29 October 2026). Every number is read from sol_results.json.
Flags: --blind (double-blind copy), --ar-abstract (standalone Arabic abstract). Writes analysis/wordcount.json on a full build."""
import json, sys, math, os, re
from docx.enum.text import WD_COLOR_INDEX
HERE = os.path.dirname(os.path.abspath(__file__)); VER = os.environ.get("MANUSCRIPT_OUT", HERE); FIGS = os.path.join(HERE, "figures")
_h = open(os.path.join(HERE, "helpers_head.py"), encoding="utf-8").read()
_h = _h.replace('R = json.load(open(f"{OUT}/results.json"))', 'R = {}').replace(
    'OUT = "/private/tmp/claude-501/-Users-mouatafaelbehairy-Desktop-business/f52f105c-d03b-4099-ad6c-6372f7dda005/scratchpad"', f'OUT = "{HERE}"')
exec(_h)
R = json.load(open(f"{HERE}/sol_results.json")); P_ = R["ports"]; AM = R["asset_moments"]; BT = R["backtest"]; ST = R["stress"]; RV = R["review"]
DR, MC, HC, DFS, BD = RV["drift"], RV["mc"], RV["hist_ci"], RV["df"], RV["backtest_dyn"]
AR = "--ar-abstract" in sys.argv
REPO_URL = "https://github.com/dr-elbehairy/solvency-var-es-insurer-capital"
WC = json.load(open(f"{HERE}/wordcount.json"))["main_text"] if os.path.exists(f"{HERE}/wordcount.json") else 8000
STEM = "Solvency_VaR_ES_Manuscript_v4"

# ---- word counting: main text = body paragraphs from Section 1 to the end of 5.3 (no headings, tables, captions, equations, references)
_counts = {"abstract": 0, "1": 0, "2": 0, "3": 0, "4": 0, "5": 0, "other": 0}; _sec = ["other"]
_P0 = P
def P(text="", **kw):
    _counts[_sec[0]] += len(re.sub(r"\*", "", text).split()); return _P0(text, **kw)
_H0 = H
def H(text, lvl=1):
    if lvl == 1:
        m = re.match(r"(\d)\.", text); _sec[0] = m.group(1) if m else ("abstract" if text == "Abstract" else "other")
    return _H0(text, lvl)
def YELLOW(text, align="c", size=11, after=8):
    p = _P0("", align=align, size=size, after=after); rr = p.add_run(text); rr.font.name = FONT; rr.font.size = Pt(size); rr.font.highlight_color = WD_COLOR_INDEX.YELLOW; return p

def pc(x, d=1): return f"{100*x:.{d}f}"
names = list(P_.keys())
short = {"Conservative (US)": "Conservative (US)", "Balanced (US)": "Balanced (US)", "Growth (US)": "Growth (US)", "EEA representative": "EEA representative",
         "Egypt insurer": "Egypt (nominal)", "Egypt insurer (real)": "Egypt (real terms)", "Saudi insurer": "Saudi"}
EG, EGR, SA, EEA, BAL, GRW, CON = (P_[k] for k in ["Egypt insurer", "Egypt insurer (real)", "Saudi insurer", "EEA representative", "Balanced (US)", "Growth (US)", "Conservative (US)"])
mature_n = ["Conservative (US)", "Balanced (US)", "Growth (US)", "EEA representative"]; mature = [P_[n] for n in mature_n]
def gap(p, m): return 100 * (p[f"{m}_ES_0.995"] - p[f"{m}_VaR_0.995"])
def mr(p, m): return 100 * p[f"{m}_VaR_0.995"] / p["G_VaR_0.995"]
g_gap = (min(gap(p, "G") for p in mature), max(gap(p, "G") for p in mature)); b_gap = (min(gap(p, "B") for p in mature), max(gap(p, "B") for p in mature))
h_over = (min(mr(p, "H") for p in mature), max(mr(p, "H") for p in mature))
cover = {n: P_[n]["SF_SCR"] - P_[n]["B_ES_0.995"] for n in names if n != "Egypt insurer (real)"}
cover0 = {n: P_[n]["SF_SCR"] - DR[n]["boot_demeaned"]["ES"] for n in names if n != "Egypt insurer (real)"}   # zero-drift coverage
sf_short = [n for n, v in cover.items() if v < 0]
lab = {"Conservative (US)": "conservative U.S.", "Balanced (US)": "balanced U.S.", "Growth (US)": "growth U.S.", "EEA representative": "EEA", "Egypt insurer": "nominal Egyptian", "Saudi insurer": "Saudi"}
def _join(xs): return ", ".join(xs[:-1]) + " and " + xs[-1] if len(xs) > 1 else (xs[0] if xs else "")
sf_short_names = _join([lab[n] for n in sf_short]); sf_short_pts = _join([f"{abs(100*cover[n]):.1f}" for n in sf_short])
bt_bal, bt_eea, bt_eg, bt_sa = BT["Balanced (US)"], BT["EEA representative"], BT["Egypt insurer"], BT["Saudi insurer"]
bd_bal, bd_eea, bd_eg, bd_sa = BD["Balanced (US)"], BD["EEA representative"], BD["Egypt insurer"], BD["Saudi insurer"]
BN = ["Balanced (US)", "EEA representative", "Egypt insurer", "Saudi insurer"]
def rej(b): return b["kupiec_p"] is not None and b["kupiec_p"] < 0.05
fhs_pass = [n for n in BN if not rej(BD[n]["fhs"])]; fhs_indep = [n for n in BN if BD[n]["fhs"]["christoffersen_p"] is not None and BD[n]["fhs"]["christoffersen_p"] >= 0.05]
real = R["egypt_real"]; egx_a = R["egx_annual"]; egp_a = R["egp_annual_depr"]; pos_years = RV["egypt_positive_real_years"]
avg_cpi = sum(real[str(y)]["cpi"] for y in range(2015, 2025)) / 10
ddf = DFS["daily"]; mdf = DFS["monthly"]; cdf = DFS["copula"]
n_df_below2 = sum(1 for v in ddf.values() if v < 2); n_df = len(ddf)
EG0 = DR["Egypt insurer"]; SA0 = DR["Saudi insurer"]
blk = {n: MC[n]["block"] for n in names}
def blk_range(n, k="ES"): v = [100 * blk[n][b][k] for b in ("20", "60", "120")]; return min(v), max(v)
seed_range = {n: (min(100 * d["ES"] for d in MC[n]["seeds"].values()), max(100 * d["ES"] for d in MC[n]["seeds"].values())) for n in names}
se_max = max(100 * MC[n]["paths100k"]["se_ES_100k"] for n in names)
kurt_list = [AM[c]["kurt"] for c in ["SPX", "STOXX", "REIT", "IGCORP", "UST", "EUGOV", "EUCORP", "EUPROP", "EGX30", "TASI", "EGDEV", "SAREIT", "SUKUK"]]

TITLE = "Value-at-Risk or Expected Shortfall for Insurer Solvency Capital? Evidence from Mature, Egyptian and Saudi Portfolios"
P(TITLE, bold=True, align="c", size=15, after=14)
if AR:
    _t = P("القيمة المعرّضة للخطر أم العجز المتوقع لرأس مال ملاءة شركات التأمين؟ أدلة من محافظ ناضجة ومصرية وسعودية", bold=True, align="c", size=14, after=12); RTL(_t)
    for _r in _t.runs: _r.font.size = Pt(15); _r.bold = True
if not BLIND:
    P("Moustafa Elbehairy ¹ *", align="c", size=12, after=2)
    P("¹ Department of Statistics and Insurance, Faculty of Commerce, Suez Canal University, Ismailia, Egypt", align="c", size=11, after=2)
    P("* Corresponding author: moustafayosri@commerce.suez.edu.eg  |  ORCID 0009-0009-1062-9420", align="c", size=11, after=10)
else:
    P("[Author details removed for double-blind review]", align="c", size=11, italic=True, after=10)
if not AR:
    P(f"Manuscript type: Quantitative research article   |   Main text ≈ {WC:,} words (Sections 1–5, excluding abstract, tables, captions and references)   |   Tables: 8   |   Figures: 5   |   JEL: G22, G28, G32, C58", align="c", size=10, after=14)

# ================================================================== ABSTRACT
if not AR:
    H("Abstract", 1)
    P(f"Solvency II sets insurer capital at a one-year value-at-risk (VaR) of 99.5 percent, a convention Egypt and Saudi Arabia are now deciding "
      f"whether to adopt. This paper measures how much the choice between VaR and expected shortfall (ES) matters once the loss "
      f"distribution is estimated from observed data, and whether a Solvency II-style market charge covers the tail. Six U.S., EEA, Egyptian and "
      f"Saudi insurer portfolios are built from {R['N_daily']:,} daily observations on eighteen series, and their one-year 99.5 percent loss is estimated "
      f"by a Gaussian model, historical simulation, a block bootstrap and a Student-t copula under two drift conventions, with daily backtests. "
      f"Under normality ES exceeds VaR by {g_gap[0]:.1f} to "
      f"{g_gap[1]:.1f} percentage points in the mature portfolios; on the bootstrap distributions the gap is {b_gap[0]:.1f} to {b_gap[1]:.1f} points and the "
      f"loss itself is larger. The Gaussian model fails every daily backtest; a filtered historical simulation passes the coverage test in all four "
      f"portfolios. For Egypt the result turns on the drift: a Gaussian VaR crediting the {pc(EG['mu_ann'])} percent nominal carry is "
      f"{pc(EG['G_VaR_0.995'])} percent, a zero-drift VaR is {pc(EG0['gauss_zero']['VaR'])} percent and the real-terms bootstrap loss is {pc(EGR['B_VaR_0.995'])} "
      f"percent, against a market charge of {pc(EG['SF_SCR'])} percent. The measure matters less than the distribution, its dynamics and the unit of "
      f"account. Egypt's Financial Regulatory Authority should calibrate its market module in real terms under a zero-drift convention, Saudi "
      f"Arabia's Insurance Authority should require ES and stressed-correlation diversification credit from 2027, and EIOPA should address "
      f"fat-tailed shortfalls through Pillar 2.", after=6)
    P("**Keywords:** Solvency II; value-at-risk; expected shortfall; risk-based capital; backtesting; Egypt; Saudi Arabia", after=10)
if AR:
    p = P("الملخص", bold=True, align="r", after=2); RTL(p)
    ar = (f"يحدد نظام Solvency II رأس مال شركات التأمين بالقيمة المعرّضة للخطر (VaR) على مدى سنة عند مستوى 99.5%، وتقف الجهات الرقابية في مصر والسعودية اليوم أمام قرار تبنّي الاتفاقية نفسها. "
          f"يقيس هذا البحث مقدار ما يترتب على الاختيار بين VaR والعجز المتوقع (ES) حين يُقدَّر توزيع الخسارة من بيانات مرصودة، وما إذا كانت شحنة مخاطر السوق على نمط Solvency II تغطي الذيل الناتج. "
          f"بُنيت ست محافظ تأمينية، ثلاث توزيعات أمريكية ومزيج ممثِّل للمنطقة الاقتصادية الأوروبية وتوزيعان مصري وسعودي يغلب عليهما الودائع، من {R['N_daily']:,} مشاهدة يومية لثماني عشرة سلسلة سوقية ورسمية، "
          f"وقُدِّرت خسارة السنة عند 99.5% بنموذج غاوسي ومحاكاة تاريخية متداخلة وبوتستراب كتلي ساكن وكوبولا t-ستيودنت، في ظل اتفاقيتين لمعاملة العائد المتوقع، مع اختبارات خلفية يومية لنماذج ساكنة وأخرى تتعقّب التقلب. "
          f"في ظل التوزيع الطبيعي يتجاوز ES قيمةَ VaR بـ {g_gap[0]:.1f} إلى {g_gap[1]:.1f} نقطة مئوية في المحافظ الناضجة؛ وعلى توزيعات البوتستراب يبلغ الفارق {b_gap[0]:.1f} إلى {b_gap[1]:.1f} نقطة والخسارة نفسها أكبر. "
          f"يخفق النموذج الغاوسي في كل الاختبارات الخلفية اليومية، بينما تجتاز المحاكاة التاريخية المرشَّحة التي تتعقّب التقلب اختبار التغطية في المحافظ الأربع. "
          f"وفي الحالة المصرية تتوقف النتيجة على معاملة العائد: فقيمة VaR الغاوسية التي تحتسب العائد الاسمي البالغ {pc(EG['mu_ann'])}% سنويًا تساوي {pc(EG['G_VaR_0.995'])}%، "
          f"وقيمة VaR بعائد صفري تساوي {pc(EG0['gauss_zero']['VaR'])}%، وخسارة البوتستراب بالقيم الحقيقية {pc(EGR['B_VaR_0.995'])}%، مقابل شحنة سوق قدرها {pc(EG['SF_SCR'])}%. "
          f"فالمقياس أقل أهمية من التوزيع وديناميكيته ووحدة القياس. ويوصي البحث الهيئةَ العامة للرقابة المالية في مصر بمعايرة وحدة مخاطر السوق بالقيم الحقيقية وباتفاقية العائد الصفري، "
          f"وهيئةَ التأمين السعودية باشتراط ES واحتساب ائتمان التنويع على ارتباطات فترات الضغط في نظام 2027، وهيئةَ EIOPA بمعالجة قصور التغطية أمام الذيول السمينة عبر الركيزة الثانية لا بتغيير مقياس الركيزة الأولى.")
    p = P(ar, align="r", after=4); RTL(p)
    p = P("الكلمات المفتاحية: Solvency II؛ القيمة المعرّضة للخطر؛ العجز المتوقع؛ رأس المال القائم على المخاطر؛ الاختبارات الخلفية؛ مصر؛ السعودية", align="r", after=12); RTL(p)
    doc.save(f"{VER}/{STEM}_الملخص_العربي.docx"); print("saved arabic abstract"); sys.exit(0)

# ================================================================== 1 INTRODUCTION
H("1.  Introduction", 1)
P("An insurer exists to absorb shocks its policyholders cannot, so the capital it must hold is defined by the worst year it is expected to survive. "
  "Solvency II writes that definition as the value-at-risk of own funds over one year at 99.5 percent (Directive 2009/138/EC, Article 101). "
  "The 2025 review, Directive (EU) 2025/2, applies from 30 January 2027 and widens the symmetric adjustment on the equity charge from ±10 to ±13 "
  "percentage points, but it leaves the measure and the confidence level where they were (European Parliament & Council, 2025; Lowet, 2026). "
  "European insurers are not short of capital against that yardstick: median SCR ratios at the end of 2024 were 230 percent for life, 216 percent "
  "for composite and 214 percent for non-life undertakings (EIOPA, 2025).", indent=True)
P("Two objections to the yardstick have been standing for a long time. Value-at-risk says what loss will not be exceeded with a given probability "
  "and nothing about the loss beyond it, and it fails sub-additivity (Artzner et al., 1999). Expected shortfall, the mean loss beyond the quantile, "
  "repairs both defects (Acerbi & Tasche, 2002), and banking regulation moved to it in 2019 (BCBS, 2019). Boonen (2017) showed that under normality "
  "the two measures are interchangeable up to a shift in the confidence level, which turns the objection into a question about distributions: the "
  "measure matters only if the tail is fat, and financial returns are (McNeil et al., 2015).", indent=True)
P("The question has stopped being European. Saudi Arabia's Insurance Authority announced on 5 April 2026 that a risk-based capital framework "
  "aligned with Solvency II becomes mandatory on 1 January 2027, after a parallel run through 2026 and five quantitative exercises (Insurance "
  "Authority, 2026a). Egypt's Unified Insurance Law No. 155 of 2024 rebuilt supervision, but the Financial Regulatory Authority's Decision No. 148 "
  "of 2025 still sets the solvency margin as the higher of 20 percent of net premiums and a claims-based figure, with no market-risk charge, for a "
  "sector whose investments reached about EGP 370 billion at the end of 2025 (FRA, 2025a, 2026). Two supervisors with very different balance "
  "sheets are taking the same design decision at the same time, and the European convention is the template each is offered.", indent=True)
P(f"This paper measures how that convention behaves on observed data. From {R['N_daily']:,} daily observations on eighteen market and official series, "
  f"among them the EGX 30, the TASI, listed Egyptian developers and Saudi REITs, a sukuk fund, the Egyptian pound, the Central Bank of Egypt's deposit "
  f"rate and SAIBOR, I build six insurer portfolios and estimate the one-year loss at 99.5 percent by four estimators that treat the tail differently. "
  f"The estimates are then set against a simplified standard-formula market charge, re-run under a zero-drift convention, checked for Monte-Carlo and "
  f"sampling error, backtested daily with static and volatility-tracking models, and, for Egypt, restated in real terms.", indent=True)
P("The contribution is threefold. (1) The risk measure, the estimator and the drift convention are varied one at a time on the same portfolios, "
  "so that the distance between VaR and ES can be separated from the distance between distributional assumptions and from a choice that supervisory "
  "practice usually leaves implicit. (2) The comparison is extended to Egyptian and Saudi insurer portfolios at the moment both markets adopt "
  "risk-based capital, in nominal and in real terms, beside U.S. and EEA benchmarks estimated on the same footing. (3) The results are turned into "
  "calibration choices addressed to the three regulators concerned.", indent=True)
P("Three questions organise the analysis. **RQ1:** How far apart are VaR and ES at the 99.5 percent calibration, and how much of the distance "
  "comes from the measure rather than from the distributional assumption? **RQ2:** Does a Solvency II-style standard formula cover the empirical "
  "tail of U.S., EEA, Egyptian and Saudi insurer portfolios? **RQ3:** What follows for risk-based capital in Egypt and Saudi Arabia? Section 2 "
  "reviews the literature and names the gap, Section 3 sets out data, estimators and the pre-announced checks, Section 4 reports the results, the "
  "robustness analysis and the discussion, and Section 5 concludes with recommendations, limitations and further research.", indent=True)

# ================================================================== 2 LITERATURE
H("2.  Literature Review", 1)
H("2.1  Solvency II and Its Market-Risk Module", 2)
P("Solvency II rests on three pillars: quantitative requirements, including the SCR and a Minimum Capital Requirement calibrated to an 85 percent "
  "VaR; governance and the Own Risk and Solvency Assessment (ORSA); and disclosure. Eling, Schmeiser and Schmit (2007) assessed the architecture "
  "while it was being negotiated, and Christiansen and Niemeyer (2014) later gave the SCR a rigorous definition. The standard formula builds the "
  "requirement from modular sub-risks; its market module aggregates interest-rate, equity, property, spread, currency and concentration charges with "
  "prescribed correlations, applying 39 percent to listed EEA and OECD equity, 49 percent to other equity, 25 percent to property and 25 percent "
  "to currency positions (Commission Delegated Regulation (EU) 2015/35). Gatzert and Martin (2012) showed that this module and an internal model "
  "can diverge widely for the same portfolio, Braun, Schmeiser and Schreiber (2017) traced the asset allocations it implicitly rewards, Höring "
  "(2013) asked whether it binds at all, and Eling and Jung (2020) and Asadi and Al Janabi (2020) measured the aggregation error of the standard "
  "approach against internal models. Grochola and Schlütter (2024) add that discretionary choices inside the formula move reported ratios "
  "materially. The market module is the focus here because it is where an insurer's asset portfolio meets the capital rules directly.", indent=True)
H("2.2  Risk Measures and Coherence", 2)
P("Let L be the one-year portfolio loss and α a confidence level. Value-at-risk is the α-quantile of the loss distribution and expected shortfall "
  "the conditional mean beyond it:", indent=True)
EQ("VaR_α = inf{ l : P(L ≤ l) ≥ α },        ES_α = E[ L | L ≥ VaR_α ]", 1)
P("Artzner et al. (1999) required a risk measure to be monotone, translation invariant, positively homogeneous and sub-additive; VaR can fail the "
  "last property, ES satisfies all four (Acerbi & Tasche, 2002; Pflug, 2000) and is convex to optimise (Rockafellar & Uryasev, 2000, 2002). VaR is "
  "elicitable and can be backtested on its own, ES is not (Gneiting, 2011), but the pair is jointly elicitable (Fissler & Ziegel, 2016), which is "
  "why ES backtests work through VaR exceedances or through the Acerbi and Székely (2014) statistics, the multinomial tests of Kratz, Lok and McNeil "
  "(2018) and the dynamic models of Patton, Ziegel and Chen (2019) (Nolde & Ziegel, 2017; Deng & Qiu, 2021). Yamai and Yoshiba (2005) warned that "
  "ES carries more estimation error than VaR when tails are fat, and Chen, Stadje and Zhang (2024) revisited the conditions under which VaR- and "
  "ES-based requirements coincide. Under a Gaussian loss with mean μ and standard deviation σ, VaR_α = σ z_α − μ and ES_α = σ φ(z_α)/(1 − α) − μ, "
  "so ES at 98.8 percent equals VaR at 99.5 percent; the measures part company only when the tail is not Gaussian (Boonen, 2017). The VaR-ES "
  "debate is therefore, in practice, a debate about distributions, and this paper treats it as one.", indent=True)
H("2.3  Estimation, Dynamics and Emerging-Market Tails", 2)
P("Whichever measure a regulator picks, the reported number depends on how the loss distribution is estimated. The variance-covariance method "
  "assumes normality and scales daily moments by the square root of time; historical simulation reads the quantile off realised returns; the "
  "stationary bootstrap of Politis and Romano (1994) and copula models rebuild the distribution while preserving clustering and tail dependence "
  "(McNeil et al., 2015). At the daily horizon the filtered historical simulation of Barone-Adesi, Giannopoulos and Vosper (1999) and the "
  "conditional extreme-value approach of McNeil and Frey (2000) showed that most of the Gaussian model's failure is a failure to track volatility, "
  "which an exponentially weighted variance (J.P. Morgan, 1996) or a GARCH filter (Bollerslev, 1986) removes. Copula-GARCH and extreme-value "
  "studies of Asian and African markets find heavier tails and stronger stress dependence than Gaussian models allow (Shim & Lee, 2016; "
  "Chaiyawat & Guayjarernpanishk, 2025; Dlamini & Shongwe, 2026), and Kim, Kim and Kim (2025) show how a skewness adjustment can be grafted "
  "onto the standard formula. For insurers the relevant horizon is a year, and aggregation over 250 trading days pulls daily fat tails toward "
  "normality unless persistence keeps them alive, which is what a block bootstrap tests.", indent=True)
H("2.4  Risk-Based Capital in Egypt and Saudi Arabia", 2)
P("Transitions to risk-based solvency in emerging markets are multi-year projects that need new supervisory tools and close work with the industry "
  "(Windsor et al., 2024). Saudi Arabia has run solvency-and-capital exercises since 2020 with eight risk categories and an equity stress of "
  "50 percent on Tadawul and OECD equities (Alzahrani, 2024), moved supervision to a dedicated Insurance Authority in 2023, and will apply a "
  "standard formula with an internal-model option from 2027; the sector's average SCR coverage was 156 percent in 2025, with a median of 142 "
  "percent, and cash and deposits were 41 percent of invested assets (Insurance Authority, 2026b; Mosa, 2025). Egypt's Decision 148/2025 keeps a "
  "premium-based margin and an intervention ladder but no market-risk charge, while the Authority's 2025 investment rules require a minimum "
  "allocation to listed equity funds (FRA, 2025a, 2025b); the determinants of Egyptian solvency margins have so far been studied through "
  "accounting ratios rather than market risk (Ahmed, Khalil & Hassan, 2024). The Egyptian balance sheet is short-dated, nominal and concentrated "
  "in sovereign paper and deposits, so its dominant risks are inflation and currency rather than equity volatility.", indent=True)
P("Read together, these strands leave two things undone. The coherence literature settles what ES is and Boonen's equivalence says when the "
  "choice is immaterial, but how far VaR and ES diverge at an insurer's one-year 99.5 percent calibration has mostly been argued on theoretical "
  "grounds or on simulated and European inputs, and the estimators have rarely been subjected to formal backtests on the same series. In the "
  "taxonomy of Müller-Bloch and Kranz (2015) and Robinson, Saldanha and McKoy (2011) that is an empirical gap. The emerging-market tail studies "
  "cover Asian and African equity but not Egyptian or Saudi insurer portfolios, with their deposit-heavy allocations and their inflation and currency "
  "regimes, at the moment both markets move to risk-based capital: a population gap. Whether a VaR convention imported from Europe captures that "
  "risk profile has not been asked with observed data, and it is the question the rest of the paper takes up.", indent=True)

# ================================================================== 3 METHODOLOGY
H("3.  Methodology", 1)
H("3.1  Research Design and Data", 2)
P("The design is a controlled comparison rather than a new model. Six portfolios are carried through the same one-year horizon and the same "
  "confidence levels, and three things are varied one at a time: the risk measure, the estimator of the loss distribution and, in Section 4.2, the "
  "drift convention. A simplified standard-formula market charge is the regulatory comparator against which the estimates are read.", indent=True)
P(f"Table 1 lists the series; each is an observed market price or an official rate. U.S. equity, listed real estate, investment-grade credit, "
  f"Treasuries and bills are the S&P 500 and the VNQ, LQD, IEF and BIL funds; euro-area equity, government bonds, corporate bonds, property and cash "
  f"are the Euro Stoxx 50 and the iShares Core EUR Government Bond, Core EUR Corporate Bond, European Property Yield and eb.rexx Money Market funds. "
  f"Egyptian equity is the EGX 30; Egyptian property is an equal-weight basket of the four largest listed developers, rebalanced daily; Egyptian "
  f"deposits accrue at the Central Bank of Egypt's overnight deposit rate on each of its decision dates; a dollar deposit is the U.S. bill return plus "
  f"the change in the pound; foreign equity is the S&P 500 in pounds. Saudi equity is the TASI, Saudi property an equal-weight basket of the twelve "
  f"Tadawul-listed REITs, sukuk the SP Funds Dow Jones Global Sukuk fund, and Saudi cash accrues at 3-month SAIBOR. Egyptian inflation is the "
  f"trailing twelve-month change in the monthly consumer price index from the {R['cpi_source']}, and the same series feeds Table 5. Prices come from "
  f"the exchanges and Yahoo Finance, the policy rate from the Central Bank's decision record and SAIBOR from the KAPSARC mirror of SAMA's statistics. "
  f"The main sample runs from {R['period_main'].replace('..', ' to ')} ({R['N_daily']:,} trading days); the Saudi portfolio starts on "
  f"{R['period_saudi'].split('..')[0]}, the first full month of the sukuk fund. Returns are continuously compounded in local currency.", indent=True)
P("The sample is chosen for the regimes it contains. Sixteen years of daily data span the aftermath of the financial crisis, the COVID crash, the "
  "2022 rates shock and, for Egypt, the November 2016 float and the 2022 to 2024 devaluations, which are the episodes a 1-in-200 calibration must be "
  "able to reproduce. The Saudi window is shorter because no observed sukuk price series exists before December 2019; Section 5.2 returns to the cost.", indent=True)
rows = []
for c, lb, src in [("SPX", "U.S. equity (S&P 500)", "Yahoo Finance"), ("REIT", "U.S. listed real estate (VNQ)", "Yahoo Finance"), ("IGCORP", "U.S. IG corporate bonds (LQD)", "Yahoo Finance"),
                   ("UST", "U.S. 7–10y Treasuries (IEF)", "Yahoo Finance"), ("TBILL", "U.S. Treasury bills (BIL)", "Yahoo Finance"), ("STOXX", "Euro-area equity (Euro Stoxx 50)", "Yahoo Finance"),
                   ("EUGOV", "Euro govt bonds (iShares Core EUR Govt)", "Xetra"), ("EUCORP", "Euro corporate bonds (iShares Core EUR Corp)", "Borsa Italiana"), ("EUPROP", "European property (iShares Eur. Property Yield)", "Xetra"),
                   ("EUCASH", "Euro money market (iShares eb.rexx)", "Xetra"), ("EGX30", "Egyptian equity (EGX 30)", "EGX"), ("EGDEV", "Egyptian developers basket (4 stocks)", "EGX"),
                   ("EGDEP", "Egyptian deposits (CBE overnight deposit rate)", "CBE decisions"), ("USD_EGP", "USD deposit in EGP terms", "Yahoo Finance"), ("SPX_EGP", "S&P 500 in EGP terms", "Yahoo Finance"),
                   ("TASI", "Saudi equity (TASI)", "Tadawul"), ("SAREIT", "Saudi REIT basket (12 funds, from Aug 2018)", "Tadawul"), ("SUKUK", "Global sukuk fund (SPSK, from Dec 2019)", "NYSE Arca"), ("SACASH", "Saudi cash (3M SAIBOR)", "SAMA / KAPSARC")]:
    a = AM[c]; rows.append([lb, src, pc(a["mu"]), pc(a["sig"]), f"{a['skew']:.2f}", f"{a['kurt']:.1f}", pc(-a["worst_day"]), pc(a["worst_year"]) if a["worst_year"] == a["worst_year"] else "–"])
TABLE("Table 1. Asset-class series, sources and daily-return moments, January 2010 to September 2026",
      ["Series (proxy)", "Source", "Mean p.a. (%)", "Vol p.a. (%)", "Skew", "Excess kurtosis", "Worst day (%)", "Worst 1-year loss (%)"], rows,
      note="Note. Annualised from daily log returns (×250 for the mean, ×√250 for volatility). Excess kurtosis is zero for a normal distribution. Worst one-year loss is the largest loss over any 250-trading-day window. EGP series are nominal local-currency returns. Series starting after January 2010 are measured from their first observation.",
      widths=[4.2, 2.8, 1.5, 1.4, 1.1, 1.5, 1.4, 1.9], size=8.5)
P("Table 2 gives the portfolios. The three U.S. allocations keep the weights of the earlier stylised literature so that the effect of replacing "
  "assumed moments with observed data can be seen directly. The EEA portfolio maps EIOPA's mid-2024 asset shares, 27 percent government bonds, "
  "29 percent corporate bonds, 22 percent equity, 4 percent funds, 5 percent cash, 7 percent mortgages and 4 percent property, onto euro-area "
  "instruments, folding mortgages into corporate credit and funds into cash (EIOPA, 2024). The Saudi portfolio follows the sector's reported mix, "
  "41 percent cash and deposits and 28 percent debt securities in 2025, rounded to 45 percent deposits, 30 percent sukuk, 20 percent equity and "
  "5 percent REITs (Insurance Authority, 2026b). For Egypt the Authority publishes no instrument breakdown for companies, so the 70 percent "
  "deposit-and-bill weight is a stylised allocation consistent with its investment rules and with the sector's known concentration in sovereign "
  "paper and deposits; the sensitivity of the Egyptian result to that weight is discussed in Section 5.2. A real-terms version of the Egyptian "
  "portfolio deflates every pound return by inflation. The diversification benefit is the Markowitz (1952) reduction of portfolio volatility below "
  "the weighted sum of stand-alone volatilities.", indent=True)
Wd = {"Conservative (US)": "S&P 10 / VNQ 5 / LQD 20 / IEF 55 / BIL 10", "Balanced (US)": "S&P 25 / VNQ 10 / LQD 20 / IEF 40 / BIL 5",
      "Growth (US)": "S&P 45 / VNQ 15 / LQD 15 / IEF 20 / BIL 5", "EEA representative": "Euro Stoxx 22 / Eur. property 4 / EUR corp 36 / EUR govt 27 / EUR cash 11",
      "Egypt insurer": "EGX 30 15 / developers 5 / EGP deposits 70 / USD deposit 5 / S&P (EGP) 5", "Egypt insurer (real)": "Same weights, all returns deflated by monthly CPI",
      "Saudi insurer": "TASI 20 / REITs 5 / sukuk 30 / SAIBOR cash 45 (2020–2026)"}
TABLE("Table 2. Portfolio weights (percent) and realised risk over each portfolio's sample",
      ["Portfolio", "Weights", "Mean p.a. (%)", "Vol p.a. (%)", "Diversification benefit (%)", "Daily skew", "Daily excess kurtosis", "Worst 1-year loss (%)"],
      [[short[n], Wd[n], pc(P_[n]["mu_ann"]), pc(P_[n]["sig_ann"]), pc(P_[n]["div_benefit"]), f"{P_[n]['skew_daily']:.2f}", f"{P_[n]['kurt_daily']:.1f}", pc(P_[n]["worst_year_hist"])] for n in names],
      note="Note. Diversification benefit = 1 − portfolio volatility ÷ weighted sum of stand-alone volatilities, full-sample daily covariance. Worst one-year loss from overlapping 250-day windows.",
      widths=[2.6, 5.2, 1.4, 1.3, 1.9, 1.2, 1.5, 1.7], size=8.5)
H("3.2  Estimators, Drift Conventions and the Regulatory Comparator", 2)
P("The estimators are the established ones of the market-risk literature, applied without modification, so that differences between the columns "
  "of Table 3 are attributable to the data. The Gaussian closed forms follow McNeil et al. (2015) and Boonen's (2017) Solvency II application; "
  "historical simulation on overlapping windows is the model-free benchmark; the stationary block bootstrap is that of Politis and Romano (1994); "
  "the Student-t copula on monthly returns follows Shim and Lee (2016). For a portfolio with weight vector w and daily log-return matrix R the "
  "portfolio return is w′R, and the Gaussian method uses annualised moments μ = 250 w′m and σ² = 250 w′Σw in", indent=True)
EQ("VaR_α = σ z_α − μ,        ES_α = σ φ(z_α)/(1 − α) − μ", 2)
P("Historical simulation takes the empirical quantile of losses over all overlapping 250-day windows. The block bootstrap resamples blocks of "
  "consecutive daily returns with geometrically distributed length of mean 60 days and compounds 250 days into a one-year return over 20,000 paths, "
  "so that clustering, autocorrelation and cross-asset dependence survive without a parametric assumption. The t-copula model fits Student-t "
  "marginals to the monthly returns of the market series and empirical marginals to the accrual and currency series, whose distributions are "
  "one-sided, couples them with a t copula whose degrees of freedom are fitted on the portfolio, and aggregates twelve simulated months over "
  "100,000 paths. VaR and ES are read off each simulated distribution at α = 0.95, 0.99 and 0.995 as", indent=True)
EQ("VaR_α = Q_α(L̂),        ES_α = mean{ L̂ : L̂ ≥ Q_α(L̂) }", 3)
P("The drift convention deserves a sentence of its own, because it is usually left implicit. Equation (2) credits the expected return μ against the "
  "loss, as does every historical or bootstrap path that compounds observed returns. Supervisory practice often sets μ to zero or to a risk-free "
  "drift, on the ground that a one-year capital charge should not be reduced by a return that is itself uncertain. Table 3 reports the with-drift "
  "convention, which is the one an insurer applying the closed forms to its own data would use; Section 4.2.1 repeats every estimator with the "
  "drift removed, by setting μ = 0 in equation (2) and by demeaning the daily series before the historical and bootstrap distributions are formed. "
  "Where the two conventions disagree, the paper says so and says which one the recommendation rests on.", indent=True)
P("The regulatory comparator is a simplified standard-formula market charge: the Delegated Regulation's shocks of 39 or 49 percent on equity by "
  "type, 25 percent on property, a parallel upward interest-rate shock of 168 basis points applied to each bond fund's published duration in "
  "place of the term-structure shock, a spread shock of 1.4 percent per year of duration on A-rated credit, a 25 percent currency shock and no "
  "charge on deposits and bills, aggregated with the prescribed correlation matrix and with the symmetric adjustment at zero. It omits the "
  "concentration sub-module and the look-through of funds, and it is labelled simplified wherever it appears.", indent=True)
H("3.3  Tests in Order, Pre-announced Robustness Checks and Code", 2)
P("The analysis proceeds in a fixed order. The daily moments of Table 1 are read first, because the size of the excess kurtosis decides whether the "
  "distributional question is live; the four one-year estimates are then compared with each other at 99.5 percent and with the comparator; and the "
  "Egyptian and Saudi portfolios are examined separately because their balance sheets differ most from the European template. Section 4.2 then "
  "reports five checks announced here. First, the drift convention of Section 3.2. Second, Monte-Carlo and sampling error: the bootstrap is re-run "
  "with 100,000 paths and batch standard errors, with mean block lengths of 20, 60 and 120 days and with three seeds, and the historical 99.5 "
  "percent quantile, which rests on about sixteen independent years, is given a block-bootstrap interval. Third, daily backtests on a rolling "
  "500-day window of six models, three static (Gaussian, variance-matched Student-t, historical) and three that track volatility through an "
  "exponentially weighted variance with λ = 0.94 (EWMA-Gaussian, EWMA-t and filtered historical simulation), using the Kupiec (1995) coverage "
  "test for 99 percent VaR, the Christoffersen (1998) independence test and the Acerbi-Székely Z₂ statistic for 97.5 percent ES, which is zero "
  "under a correct ES and positive when ES is too low. Fourth, diversification benefits recomputed inside five stress windows. Fifth, the "
  "Egyptian portfolio restated in real terms. Student-t degrees of freedom are reported for every series at the daily and monthly horizon and for "
  "each copula, since the claim that tails are fat should be visible in them.", indent=True)
P("The backtests deserve a word on mechanics, because their verdicts carry much of the argument. On each day after the first 500 the model is "
  "re-estimated on the preceding 500 returns and produces a 99 percent VaR and a 97.5 percent ES for the next day; an exceedance is a loss above the "
  "VaR. Kupiec's statistic compares the observed exceedance rate with 1 percent by a likelihood ratio, Christoffersen's compares the probability of an "
  "exceedance after an exceedance with the probability after a quiet day, and Z₂ averages the ratio of realised losses to the forecast ES over the days "
  "on which the 97.5 percent VaR was breached. For the EWMA models the conditional variance is σ²ₜ = λσ²ₜ₋₁ + (1 − λ)r²ₜ₋₁, the Student-t degrees of "
  "freedom are refitted every twenty days on the window's standardised residuals, and filtered historical simulation scales the empirical quantiles of "
  "those residuals by the current σₜ. No GARCH parameters are estimated; the point of the exercise is to see how much of the static models' failure a "
  "one-parameter filter removes.", indent=True)
P(f"All computations use Python 3.11 with NumPy, SciPy and pandas; the bootstrap and copula simulations are seeded (2026), so every figure "
  f"reproduces to the digit. " + ("The scripts, the aligned daily data, the simulation outputs and the environment specification are available in a public repository (link withheld for review)."
  if BLIND else f"The scripts, the aligned daily data, the simulation outputs and the environment specification are openly available at {REPO_URL} (release v1.0.0)."), indent=True)
if not BLIND: YELLOW("Zenodo DOI: to be inserted after release", align="l", size=11, after=6)

# ================================================================== 4 EMPIRICAL ANALYSIS
H("4.  Empirical Analysis", 1)
H("4.1  Results", 2)
H("4.1.1  Fat Tails in the Data", 3)
P(f"Table 1 shows why the distributional question comes first. Every market series has excess kurtosis far above zero, from {min(kurt_list):.1f} for "
  f"Treasuries to {max(kurt_list):.0f} for investment-grade corporate bonds, whose March 2020 dislocation produced moves a normal model would call "
  f"impossible. Student-t fits to the standardised daily returns return degrees of freedom between {min(ddf.values()):.1f} and {max(ddf.values()):.1f}, "
  f"below two for {n_df_below2} of the {n_df} series, which is to say that at the daily horizon not even the variance is comfortably finite; at the "
  f"monthly horizon the fits recover to {min(mdf.values()):.1f}–{max(mdf.values()):.0f}, and the copula degrees of freedom fitted on the portfolios lie between "
  f"{min(cdf.values()):.1f} and {max(cdf.values()):.1f}. The EGX 30 is the most volatile equity series at {pc(AM['EGX30']['sig'])} percent a year, with a worst "
  f"one-year loss of {pc(AM['EGX30']['worst_year'])} percent, yet its annual returns are dominated by two currency-driven surges, {pc(egx_a.get('2016', 0), 0)} "
  f"percent in 2016 and {pc(egx_a.get('2023', 0), 0)} percent in 2023, in years in which the pound lost {pc(egp_a.get('2016', 0), 0)} and {pc(egp_a.get('2023', 0), 0)} "
  f"percent against the dollar (Figure 1). The dollar-deposit series has a skewness of {AM['USD_EGP']['skew']:.0f}, because its return is a step function "
  f"of three devaluations; a symmetric model would invent appreciations that never happened, which is why the copula uses an empirical marginal for it. "
  f"The TASI is calmer, at {pc(AM['TASI']['sig'])} percent volatility, but its excess kurtosis of {AM['TASI']['kurt']:.0f} is no lower than that of the S&P 500 "
  f"({AM['SPX']['kurt']:.0f}) and its worst one-year loss, {pc(AM['TASI']['worst_year'])} percent, is larger.", indent=True)
FIG(f"{FIGS}/fig1_indices.png", "Figure 1. Equity indices and the Egyptian pound, January 2010 to September 2026, rebased to 1 (log scale, upper panel) and drawdowns from peak "
    "(lower panel). Dotted lines mark the November 2016 float, the COVID trough, the March 2022 devaluation and the March 2024 float. Sources: exchanges, Yahoo Finance.", width_cm=14.5)
H("4.1.2  VaR and ES at the Solvency II Calibration", 3)
P(f"Table 3 reports the one-year 99.5 percent estimates under the with-drift convention. Under the Gaussian model the ES-VaR gap is modest, "
  f"{g_gap[0]:.1f} to {g_gap[1]:.1f} percentage points for the U.S. and EEA portfolios and {gap(EG,'G'):.1f} points for Egypt, which is Boonen's (2017) result "
  f"reproduced on market data and would by itself justify regulatory indifference between the measures. The Gaussian estimate is also the lowest in "
  f"almost every cell. The historical 99.5 percent loss runs {h_over[0]:.0f} to {h_over[1]:.0f} percent of the Gaussian VaR in the mature portfolios and the "
  f"bootstrap ES exceeds the Gaussian ES by {min(100*(p['B_ES_0.995']-p['G_ES_0.995']) for p in mature):.1f} to {max(100*(p['B_ES_0.995']-p['G_ES_0.995']) for p in mature):.1f} "
  f"points; the bootstrap ES-VaR gap of {b_gap[0]:.1f} to {b_gap[1]:.1f} points is roughly double its Gaussian counterpart. The gap opens not because ES is a "
  f"more conservative measure but because the empirical distribution has more mass beyond the quantile. The t-copula on monthly returns sits close to "
  f"the Gaussian figure for the mature portfolios: monthly fat tails wash out over twelve independent months, and what keeps the annual tail fat is the "
  f"persistence that the block bootstrap and the historical windows preserve.", indent=True)
P(f"The lower confidence levels, reported in the repository, show where the two estimators part company. At 95 percent the Gaussian and bootstrap "
  f"VaR of the balanced portfolio are {pc(BAL['G_VaR_0.95'])} and {pc(BAL['B_VaR_0.95'])} percent, close enough to make the choice of estimator look "
  f"academic; at 99 percent they are {pc(BAL['G_VaR_0.99'])} and {pc(BAL['B_VaR_0.99'])} percent, and at 99.5 percent {pc(BAL['G_VaR_0.995'])} and "
  f"{pc(BAL['B_VaR_0.995'])} percent. The divergence grows with the level because the normal density thins out faster than the resampled one, and the "
  f"ES increment grows with it: the bootstrap ES-VaR gap of the balanced portfolio is {100*(BAL['B_ES_0.95']-BAL['B_VaR_0.95']):.1f} points at 95 percent and "
  f"{gap(BAL, 'B'):.1f} at 99.5. A supervisor who calibrates at 99.5 percent is therefore working exactly where the distributional assumption bites "
  f"hardest, which is the practical reason the question of this paper cannot be settled at the 95 percent level on which much of the market-risk "
  f"literature reports.", indent=True)
def rowfor(n):
    p = P_[n]; return [short[n]] + [f"{pc(p[f'{m}_VaR_0.995'])} / {pc(p[f'{m}_ES_0.995'])}" for m in ["G", "H", "B", "T"]] + [pc(p["SF_SCR"] if n != "Egypt insurer (real)" else EG["SF_SCR"])]
TABLE("Table 3. One-year VaR / ES at 99.5 percent by estimation method, with-drift convention (percent of portfolio value), and the simplified standard-formula market charge",
      ["Portfolio", "Gaussian VaR / ES", "Historical VaR / ES", "Block bootstrap VaR / ES", "t-copula (monthly) VaR / ES", "Simplified standard-formula charge"],
      [rowfor(n) for n in names],
      note="Note. Bootstrap: 20,000 one-year paths, mean block length 60 days. t-copula: 100,000 paths of twelve months. The standard-formula charge is computed as in Section 3.2 with the symmetric adjustment at zero; "
           "it has no inflation module, so the nominal Egyptian figure is repeated for the real-terms portfolio. Estimates at 95 and 99 percent are in the repository.",
      widths=[3.0, 2.4, 2.4, 2.6, 2.8, 2.6], size=8.5)
FIG(f"{FIGS}/fig2_methods.png", "Figure 2. One-year 99.5 percent VaR (solid) and the ES increment (hatched) by estimation method under the with-drift convention, with the simplified standard-formula market charge as comparator (diamonds).", width_cm=15)
H("4.1.3  The Egyptian and Saudi Portfolios", 3)
P(f"The Egyptian portfolio earns a nominal carry of {pc(EG['mu_ann'])} percent a year, almost all of it from deposits and bills, and under the with-drift "
  f"Gaussian model that cushion pushes the 99.5 percent VaR to {pc(EG['G_VaR_0.995'])} percent: the model cannot construct a losing year. The bootstrap, "
  f"which keeps the 2016 and 2022–2024 episodes intact, puts the VaR at {pc(EG['B_VaR_0.995'])} percent and the ES at {pc(EG['B_ES_0.995'])} percent; the "
  f"historical estimate is {pc(EG['H_VaR_0.995'])} / {pc(EG['H_ES_0.995'])} percent. Real terms tell a different story. Deposit rates were below inflation in "
  f"every year from 2015 to 2024 except {_join([str(y) for y in pos_years if y <= 2024])} (Table 5), with real returns of {pc(real['2017']['real'])} percent in 2017 "
  f"and {pc(real['2023']['real'])} percent in 2023, so the real-terms portfolio has an expected return of {pc(EGR['mu_ann'])} percent and a bootstrap 99.5 percent "
  f"loss of {pc(EGR['B_VaR_0.995'])} percent, with an ES of {pc(EGR['B_ES_0.995'])} percent (Figure 3). Section 4.2.1 shows that the negative nominal VaR is a "
  f"property of the drift convention rather than of the balance sheet. The Saudi portfolio, estimated on 2020 to 2026, behaves like a conservative "
  f"developed-market allocation: a Gaussian 99.5 percent VaR of {pc(SA['G_VaR_0.995'])} percent, a bootstrap VaR of {pc(SA['B_VaR_0.995'])} and ES of "
  f"{pc(SA['B_ES_0.995'])} percent, and a comparator charge of {pc(SA['SF_SCR'])} percent. The Authority's own 50 percent equity stress alone implies "
  f"{pc(SA['SaudiRBC_equity50'])} percent for these weights. Two features of the Saudi row deserve notice. The historical estimate, {pc(SA['H_VaR_0.995'])} / "
  f"{pc(SA['H_ES_0.995'])} percent, is the lowest in the row and lower than the Gaussian figure, the only portfolio for which that happens; it is read "
  f"from {SA['N']:,} trading days, roughly {SA['N']/250:.1f} years, so its 99.5 percent quantile is close to the single worst window the sample contains, "
  f"and Table 6 shows how wide its interval is. The bootstrap, by recombining the COVID and 2022 blocks in orders the sample never produced, is the "
  f"estimator that extrapolates beyond that window, and the t-copula ({pc(SA['T_VaR_0.995'])} / {pc(SA['T_ES_0.995'])} percent, {cdf['Saudi insurer']:.1f} degrees of "
  f"freedom) sits between the two. For a supervisor with a short observed history the ordering is itself informative: the estimator that is usually "
  f"described as model-free is here the one most bound by the sample.", indent=True)
FIG(f"{FIGS}/fig3_lossdist.png", "Figure 3. Bootstrapped one-year loss distributions (20,000 paths) with the Gaussian VaR under the with-drift (dotted) and zero-drift (dash-dot) conventions, the bootstrap VaR (dashed) and the bootstrap ES (solid) at 99.5 percent, for the EEA, Egyptian nominal, Egyptian real-terms and Saudi portfolios.", width_cm=16)
H("4.1.4  What the Standard Formula Covers", 3)
P(f"The last column of Table 3 answers RQ2 under the with-drift convention. For the mature portfolios the simplified charge lies between the Gaussian "
  f"and the historical estimates: it covers the Gaussian ES in every case and the bootstrap ES in "
  f"{sum(1 for n in mature_n if cover[n] >= 0)} of the four, falling short of the bootstrap ES by {_join([f'{abs(100*cover[n]):.1f}' for n in mature_n if cover[n] < 0])} points for the "
  f"{_join([lab[n] for n in mature_n if cover[n] < 0])} portfolios. The 49 percent shock on non-OECD equity makes the charge sufficient for the Saudi "
  f"portfolio, by {100*cover['Saudi insurer']:.1f} points over the bootstrap ES, and for the Egyptian portfolio in nominal terms by {100*cover['Egypt insurer']:.1f} "
  f"points; in real terms a charge of {pc(EG['SF_SCR'])} percent stands against a loss of {pc(EGR['B_VaR_0.995'])} percent. The formula was designed for "
  f"balance sheets whose dominant market risk is equity and duration, and it charges nothing on deposits and bills; for a balance sheet whose dominant "
  f"risk is the real value of short-dated sovereign paper it measures the wrong thing. How much of this conclusion survives the removal of the drift "
  f"is the first question of the next section.", indent=True)
P(f"The composition of the charge explains its pattern. For the Egyptian weights the comparator is built from an equity sub-charge of "
  f"{100*EG['SF_parts']['equity']:.1f} points, a property sub-charge of {100*EG['SF_parts']['property']:.1f} and a currency sub-charge of {100*EG['SF_parts']['currency']:.1f}, "
  f"with nothing at all on the 70 percent held in deposits and bills, which carry no interest-rate or spread charge at their duration; the prescribed "
  f"correlations reduce the simple sum of {100*sum(EG['SF_parts'].values()):.1f} points to {pc(EG['SF_SCR'])}. For the Saudi weights the equity sub-charge is "
  f"the same {100*SA['SF_parts']['equity']:.1f} points, joined by {100*SA['SF_parts']['interest']:.1f} points of interest-rate and {100*SA['SF_parts']['spread']:.1f} of "
  f"spread risk on the sukuk. For the conservative U.S. portfolio, by contrast, {100*CON['SF_parts']['interest']:.1f} of the {pc(CON['SF_SCR'])} points come from "
  f"the interest-rate module and only {100*CON['SF_parts']['equity']:.1f} from equity, and the charge still falls {abs(100*cover['Conservative (US)']):.1f} points "
  f"short of the bootstrap ES, because the March 2020 credit dislocation and the 2022 bond sell-off sit in the data and not in a 168 basis-point "
  f"parallel shock. The formula is severe where the shock is severe and silent where it has no module, and the Egyptian and Saudi balance sheets "
  f"happen to sit mostly in the silent part.", indent=True)

H("4.2  Robustness and Sensitivity", 2)
H("4.2.1  The Drift Convention", 3)
P(f"Table 4 repeats the Gaussian, historical and bootstrap estimates with the drift removed. For the mature portfolios the zero-drift Gaussian VaR "
  f"rises by the expected return, {pc(CON['mu_ann'])} to {pc(GRW['mu_ann'])} points, and moves toward the historical and bootstrap figures; the ordering "
  f"of the estimators and the doubling of the ES-VaR gap on the empirical distributions are unchanged. For Egypt the convention is decisive. With "
  f"μ = 0 the Gaussian 99.5 percent VaR is {pc(EG0['gauss_zero']['VaR'])} percent and the ES {pc(EG0['gauss_zero']['ES'])} percent; the demeaned bootstrap gives "
  f"{pc(EG0['boot_demeaned']['VaR'])} / {pc(EG0['boot_demeaned']['ES'])} percent and the demeaned historical windows {pc(EG0['hist_demeaned']['VaR'])} / "
  f"{pc(EG0['hist_demeaned']['ES'])} percent. These figures are of the same order as the real-terms estimates of Table 3 ({pc(EGR['B_VaR_0.995'])} / "
  f"{pc(EGR['B_ES_0.995'])} percent), which is not a coincidence: the nominal carry is largely compensation for inflation, so stripping the drift and "
  f"deflating the returns are two routes to the same correction. The only estimate that describes the Egyptian insurer as almost riskless is the "
  f"nominal Gaussian VaR that credits the carry and ignores what the carry compensates for. The coverage verdict changes with it. Under zero drift the "
  f"simplified charge of {pc(EG['SF_SCR'])} percent falls short of the demeaned bootstrap ES by {abs(100*cover0['Egypt insurer']):.1f} points in nominal terms, "
  f"and for Saudi Arabia the margin of {100*cover['Saudi insurer']:.1f} points over the with-drift bootstrap ES becomes a shortfall of "
  f"{abs(100*cover0['Saudi insurer']):.1f} points against the demeaned one ({pc(SA0['boot_demeaned']['ES'])} percent), although the zero-drift Gaussian ES "
  f"({pc(SA0['gauss_zero']['ES'])} percent) remains covered. Section 5.1 states which convention each recommendation rests on.", indent=True)
def drow(n):
    d = DR[n]; p = P_[n]
    return [short[n], pc(d["mu_ann"]), f"{pc(d['gauss_mu']['VaR'])} / {pc(d['gauss_mu']['ES'])}", f"{pc(d['gauss_zero']['VaR'])} / {pc(d['gauss_zero']['ES'])}",
            f"{pc(p['H_VaR_0.995'])} / {pc(p['H_ES_0.995'])}", f"{pc(d['hist_demeaned']['VaR'])} / {pc(d['hist_demeaned']['ES'])}",
            f"{pc(p['B_VaR_0.995'])} / {pc(p['B_ES_0.995'])}", f"{pc(d['boot_demeaned']['VaR'])} / {pc(d['boot_demeaned']['ES'])}"]
TABLE("Table 4. One-year 99.5 percent VaR / ES under the with-drift and zero-drift conventions (percent of portfolio value)",
      ["Portfolio", "Drift μ (% p.a.)", "Gaussian, with drift", "Gaussian, μ = 0", "Historical, with drift", "Historical, demeaned", "Bootstrap, with drift", "Bootstrap, demeaned"],
      [drow(n) for n in names],
      note="Note. Zero-drift Gaussian sets μ = 0 in equation (2); demeaned historical and bootstrap distributions are formed from daily returns net of their sample mean. Same seed and block length as Table 3.",
      widths=[2.6, 1.5, 1.9, 1.7, 1.9, 1.9, 1.9, 1.9], size=8.5)
TABLE("Table 5. Egyptian deposit rates, inflation and real returns, 2015–2024",
      ["Year", "Deposit rate (%)", "CPI inflation (%)", "Real deposit return (%)", "EGX 30 return (%)", "EGP per USD change (%)"],
      [[str(y), pc(real[str(y)]["deposit"]), pc(real[str(y)]["cpi"]), pc(real[str(y)]["real"]), pc(egx_a.get(str(y), float('nan'))), pc(egp_a.get(str(y), float('nan')))] for y in range(2015, 2025)],
      note=f"Note. Deposit rate from the Central Bank of Egypt's decision record (daily accrual averaged by year); inflation from the {R['cpi_source']}; index and currency changes from year-end closes. A positive currency change is a depreciation of the pound.",
      widths=[1.4, 2.4, 2.4, 2.8, 2.6, 2.8], size=9)
H("4.2.2  Monte-Carlo and Sampling Error", 3)
P(f"Table 6 reports how much of each estimate is noise. Monte-Carlo error is negligible: with 100,000 bootstrap paths the batch standard error of the "
  f"99.5 percent ES is at most {se_max:.2f} points, and the three seeds move the 20,000-path ES by no more than {max(b-a for a,b in seed_range.values()):.1f} points in "
  f"any portfolio. The block length matters more. Moving the mean block from 20 to 120 days changes the bootstrap ES by {blk_range('Conservative (US)')[1]-blk_range('Conservative (US)')[0]:.1f} "
  f"points for the conservative U.S. portfolio and by {blk_range('Balanced (US)')[1]-blk_range('Balanced (US)')[0]:.1f} for the balanced one, in the direction longer "
  f"blocks imply, because longer blocks carry more of the persistence that fattens the annual tail; for the Egyptian and Saudi portfolios the range is "
  f"under {max(blk_range('Egypt insurer')[1]-blk_range('Egypt insurer')[0], blk_range('Saudi insurer')[1]-blk_range('Saudi insurer')[0])+0.05:.1f} point. The historical "
  f"estimate is the least precise of all. Its 99.5 percent quantile is read from about {HC['Balanced (US)']['indep_years']:.0f} independent years, and a block "
  f"bootstrap of the daily series gives a 95 percent interval of {pc(HC['Conservative (US)']['lo'])} to {pc(HC['Conservative (US)']['hi'])} percent around the "
  f"{pc(HC['Conservative (US)']['point'])} percent point estimate for the conservative portfolio and {pc(HC['Balanced (US)']['lo'])} to {pc(HC['Balanced (US)']['hi'])} "
  f"percent for the balanced one. The claim that the historical loss runs {h_over[0]:.0f} to {h_over[1]:.0f} percent of the Gaussian VaR is therefore a statement "
  f"about point estimates whose lower confidence bounds lie below the Gaussian figure; the evidence that the Gaussian model understates the tail has to "
  f"come from the daily backtests, where the sample is large enough to carry it.", indent=True)
def mrow(n):
    m = MC[n]; h = HC[n]; b = blk[n]
    return [short[n], f"{pc(m['paths100k']['VaR'])} / {pc(m['paths100k']['ES'])}", f"{100*m['paths100k']['se_ES_100k']:.2f}",
            f"{pc(b['20']['ES'])} / {pc(b['60']['ES'])} / {pc(b['120']['ES'])}", f"{seed_range[n][0]:.1f}–{seed_range[n][1]:.1f}", pc(h["point"]), f"{pc(h['lo'])} to {pc(h['hi'])}"]
TABLE("Table 6. Monte-Carlo and sampling error of the empirical estimators at 99.5 percent (percent of portfolio value)",
      ["Portfolio", "Bootstrap VaR / ES, 100,000 paths", "Batch s.e. of ES", "Bootstrap ES by mean block 20 / 60 / 120 days", "ES range over three seeds (20,000 paths)", "Historical VaR, point", "Historical VaR, 95% block-bootstrap interval"],
      [mrow(n) for n in names],
      note="Note. Batch standard error from ten batches of 10,000 paths. Historical interval from 300 stationary-bootstrap replications (mean block 60 days) of the daily series, each re-forming the overlapping 250-day windows.",
      widths=[2.6, 2.3, 1.5, 2.6, 2.3, 1.7, 2.5], size=8.5)
H("4.2.3  Daily Backtests: Static and Volatility-Tracking Models", 3)
P(f"Table 7 and Figure 5 report the daily backtests, where {bt_bal['gauss']['T']:,} out-of-sample days ({bt_sa['gauss']['T']:,} for Saudi Arabia) are enough to "
  f"test what the annual results can only suggest. The static Gaussian model records {bt_bal['gauss']['exceedances']} exceedances of the 99 percent VaR for the "
  f"balanced portfolio against {bt_bal['gauss']['expected']:.0f} expected, {bt_eea['gauss']['exceedances']} for the EEA portfolio, {bt_eg['gauss']['exceedances']} for "
  f"the Egyptian and {bt_sa['gauss']['exceedances']} against {bt_sa['gauss']['expected']:.0f} for the Saudi, and Kupiec rejects it everywhere; its Z₂ statistics of "
  f"{min(bt_bal['gauss']['AS_Z2'], bt_sa['gauss']['AS_Z2'], bt_eea['gauss']['AS_Z2'], bt_eg['gauss']['AS_Z2']):.2f} to {max(bt_bal['gauss']['AS_Z2'], bt_sa['gauss']['AS_Z2'], bt_eea['gauss']['AS_Z2'], bt_eg['gauss']['AS_Z2']):.2f} "
  f"mean that realised tail losses exceeded the Gaussian ES by roughly half to double. The variance-matched Student-t, refitted on each window, cuts "
  f"the exceedances to {bt_bal['t']['exceedances']}, {bt_eea['t']['exceedances']}, {bt_eg['t']['exceedances']} and {bt_sa['t']['exceedances']} but is still rejected "
  f"except for Saudi Arabia, and its fitted degrees of freedom sit at the floor of the grid, three, in almost every window. The static historical model "
  f"comes closest to the nominal rate, with {bt_bal['hist']['exceedances']}, {bt_eea['hist']['exceedances']}, {bt_eg['hist']['exceedances']} and "
  f"{bt_sa['hist']['exceedances']} exceedances. In all three the Christoffersen test rejects independence: exceedances arrive in clusters, in 2020, in 2022 "
  f"and, for Egypt, around each devaluation.", indent=True)
P(f"The volatility-tracking models say what the clusters mean. An EWMA variance under a Gaussian tail changes almost nothing ({bd_bal['ewma_gauss']['exceedances']}, "
  f"{bd_eea['ewma_gauss']['exceedances']}, {bd_eg['ewma_gauss']['exceedances']} and {bd_sa['ewma_gauss']['exceedances']} exceedances), and under a Student-t tail it "
  f"removes part of the excess ({bd_bal['ewma_t']['exceedances']}, {bd_eea['ewma_t']['exceedances']}, {bd_eg['ewma_t']['exceedances']} and {bd_sa['ewma_t']['exceedances']}) "
  f"without passing. Filtered historical simulation, which scales the empirical distribution of standardised residuals by the current volatility, "
  f"records {bd_bal['fhs']['exceedances']}, {bd_eea['fhs']['exceedances']}, {bd_eg['fhs']['exceedances']} and {bd_sa['fhs']['exceedances']} exceedances, passes the "
  f"Kupiec test in {['none', 'one', 'two', 'three', 'all four'][len(fhs_pass)]} portfolios, has Z₂ statistics of {min(BD[n]['fhs']['AS_Z2'] for n in BN):.2f} to "
  f"{max(BD[n]['fhs']['AS_Z2'] for n in BN):.2f}, and passes the independence test in {['none', 'one', 'two', 'three', 'all four'][len(fhs_indep)]} of them "
  f"(the exception is the balanced U.S. portfolio, p = {bd_bal['fhs']['christoffersen_p']:.3f}). The failure documented in Table 7 is therefore not a "
  f"failure of parametric models as such but of models that fix either the shape of the tail or the level of volatility: what reproduces the daily tail "
  f"is an empirical shape with a time-varying scale, which is the daily counterpart of the persistence the block bootstrap preserves at the annual "
  f"horizon.", indent=True)
P(f"Two details of the dynamic models qualify this reading. The EWMA-t degrees of freedom, refitted every twenty days on the standardised residuals, "
  f"have a median of {bd_bal['t_df_median']:.0f} for the balanced portfolio and {bd_sa['t_df_median']:.0f} for the Saudi one and range from {bd_bal['t_df_min']:.0f} to "
  f"{max(b['t_df_max'] for b in BD.values()):.0f}, so filtering removes some but not all of the daily fat tail; the residual tail is what the filtered "
  f"historical model captures and the Gaussian filter does not. And the real-terms Egyptian portfolio, backtested on the same rolling window, behaves like "
  f"the nominal one ({BD['Egypt insurer (real)']['ewma_gauss']['exceedances']}, {BD['Egypt insurer (real)']['ewma_t']['exceedances']} and "
  f"{BD['Egypt insurer (real)']['fhs']['exceedances']} exceedances for the three dynamic models), because deflating by a smooth monthly inflation series "
  f"changes the level of the loss distribution far more than its daily shape. The daily evidence therefore says nothing about the unit of account, "
  f"which is a one-year question, and everything about the dynamics, which the one-year estimators can only carry through the block structure.", indent=True)
def btrow(n, k, src, labk):
    b = src[n][k]; return [short[n], labk, str(b["exceedances"]), f"{b['expected']:.0f}", f"{100*b['rate']:.2f}",
                           f"{b['kupiec_p']:.3f}" if b["kupiec_p"] is not None else "–", f"{b['christoffersen_p']:.3f}" if b["christoffersen_p"] is not None else "–", f"{b['AS_Z2']:.2f}"]
btrows = []
for n in BN:
    for k, labk in [("gauss", "Gaussian (static)"), ("t", "Student-t (static)"), ("hist", "Historical (static)")]: btrows.append(btrow(n, k, BT, labk))
    for k, labk in [("ewma_gauss", "EWMA-Gaussian"), ("ewma_t", "EWMA-t"), ("fhs", "Filtered historical")]: btrows.append(btrow(n, k, BD, labk))
TABLE("Table 7. Daily backtests of 99 percent VaR and 97.5 percent ES, rolling 500-day estimation window, static and volatility-tracking models",
      ["Portfolio", "Model", "Exceedances", "Expected", "Rate (%)", "Kupiec p", "Christoffersen p", "Acerbi–Székely Z₂"], btrows,
      note=f"Note. Kupiec tests the unconditional exceedance rate against 1 percent; Christoffersen tests independence of exceedances; Z₂ is zero under a correct ES and positive when ES is too low. "
           f"EWMA models use λ = 0.94 with the Student-t degrees of freedom refitted on the window's standardised residuals; filtered historical simulation scales the empirical quantiles of those residuals by the current volatility. "
           f"Test window: {bt_bal['gauss']['T']:,} days ({bt_sa['gauss']['T']:,} for Saudi Arabia).", widths=[2.4, 2.6, 1.6, 1.4, 1.3, 1.5, 1.9, 1.9], size=8)
FIG(f"{FIGS}/fig5_backtests.png", "Figure 5. Daily 99 percent VaR exceedances divided by the expected number, by model and portfolio; the dashed line marks correct coverage.", width_cm=15)
H("4.2.4  Diversification in Stress Windows", 3)
P(f"Table 8 and Figure 4 report the diversification benefit in the full sample and in five stress windows. The full-sample benefit runs from "
  f"{pc(min(P_[n]['div_benefit'] for n in names))} to {pc(max(P_[n]['div_benefit'] for n in names))} percent. In the COVID window it falls to "
  f"{pc(min(ST[n]['COVID 2020'][0] for n in names if 'real' not in n))}–{pc(max(ST[n]['COVID 2020'][0] for n in names if 'real' not in n))} percent and in the 2022 rates "
  f"shock, when bonds and equities fell together, to {pc(min(ST[n]['Rates shock 2022'][0] for n in names if 'real' not in n))}–{pc(max(ST[n]['Rates shock 2022'][0] for n in names if 'real' not in n))} "
  f"percent. The Egyptian portfolio runs the other way: in the devaluation windows its measured benefit holds or rises, because the dollar deposit "
  f"and the equity index both jump when the pound falls, so the asset that protects the insurer in a currency crisis looks, in a calm-period "
  f"covariance matrix, like an undiversified bet. Capital relief for diversification should be estimated on stressed rather than average "
  f"correlations, which is what the bootstrap does implicitly and the standard formula does through its fixed matrix. The Saudi figures make the "
  f"point in the form the Authority will meet it: a benefit of {pc(ST['Saudi insurer']['full'][0])} percent in the full sample becomes {pc(ST['Saudi insurer']['COVID 2020'][0])} "
  f"percent in the COVID window and {pc(ST['Saudi insurer']['Rates shock 2022'][0])} percent in 2022, while the same window hardly touches the Egyptian "
  f"figure ({pc(ST['Egypt insurer']['full'][0])} percent in the full sample, {pc(ST['Egypt insurer']['Egypt 2022-24 devaluations'][0])} percent during the "
  f"2022–2024 devaluations), because the Egyptian stress is a currency event in which the hedge and the hedged asset move together.", indent=True)
TABLE("Table 8. Diversification benefit by portfolio in the full sample and in five stress windows (percent)",
      ["Portfolio", "Full sample", "2010–11", "COVID 2020", "Rates 2022", "Egypt float 2016–17", "Egypt 2022–24"],
      [[short[n]] + [(pc(ST[n][k][0]) if ST[n][k][0] == ST[n][k][0] else "–") for k in ["full", "GFC aftermath 2010-11", "COVID 2020", "Rates shock 2022", "Egypt float 2016-17", "Egypt 2022-24 devaluations"]] for n in names],
      note="Note. Benefit = 1 − portfolio volatility ÷ weighted sum of stand-alone volatilities, computed from daily returns inside each window; dashes mark windows before a portfolio's sample starts.", widths=[3.2, 1.9, 1.7, 1.9, 1.8, 2.6, 2.3], size=9)
FIG(f"{FIGS}/fig4_divers.png", "Figure 4. Diversification benefit in the full sample and in five stress windows.", width_cm=14.5)

H("4.3  Discussion", 2)
P("The results settle the VaR-ES question in a way neither side of the debate quite expects. If returns were Gaussian, moving Solvency II from VaR "
  "to ES at the same confidence level would add one to three points of capital in developed-market portfolios and could be undone by a small change "
  "in the confidence level, as Boonen (2017) argued. Returns are not Gaussian, and once a model preserves the tail, by reading history directly or by "
  "resampling it in blocks, both measures rise and the gap between them roughly doubles. The largest single error in Table 3 is not the choice of "
  "measure but the normal distribution, which understates the historical 99.5 percent loss of the conservative portfolio by nearly half; and Section "
  "4.2.2 adds the caveat that the historical point estimate carries a wide interval, so the weight of that conclusion rests on the backtests, where "
  "the Gaussian model is rejected without exception.", indent=True)
P("Set against Section 2, the findings agree with Boonen exactly where his argument applies and part from it where it does not: the equivalence of "
  "ES at 98.8 percent and VaR at 99.5 percent holds for the Gaussian column and for none of the others. They agree with Yamai and Yoshiba (2005) that "
  "ES is the harder quantity to estimate, which is why Table 6 reports Monte-Carlo and block-length error and finds the latter larger than the "
  "former. They qualify the banking precedent (BCBS, 2019): a move to ES at a lower confidence level buys something only if the distribution behind "
  "it admits fat tails. And they place the daily evidence squarely in the line of Barone-Adesi et al. (1999) and McNeil and Frey (2000): a filtered "
  "historical simulation passes the coverage test in every portfolio while static models of either shape fail, so the clustering that Christoffersen's "
  "test detects is a modelling problem with a known solution, not an argument against parametric risk measurement. The emerging-market tail studies "
  "(Shim & Lee, 2016; Chaiyawat & Guayjarernpanishk, 2025; Dlamini & Shongwe, 2026) are confirmed for Egypt, where the mechanism is the joint jump of "
  "the currency and the equity index, and qualified for Saudi Arabia, whose deposit-and-sukuk portfolio under a dollar peg behaves like a conservative "
  "developed-market allocation.", indent=True)
P("The standard formula performs better than its critics suggest for the balance sheets it was designed for, and the drift analysis sharpens where it "
  "does not. Its market charge covers the Gaussian estimates for every portfolio and, under the with-drift convention, the bootstrap estimates for the "
  "deposit-heavy Saudi and nominal Egyptian portfolios, largely because the 49 percent shock on non-OECD equity is severe. It falls short of the "
  "historical tail for the equity-heavy U.S. portfolios, which is the basis risk Gatzert and Martin (2012) and Braun et al. (2017) describe from the "
  "other side, and it has nothing to say about inflation, because in the euro area of 2009 inflation was not a solvency risk. Once the drift is "
  "removed the Egyptian shortfall appears in nominal terms as well, and the Saudi margin narrows to a small deficit against the demeaned bootstrap. "
  "Kim, Kim and Kim's (2025) skewness adjustment targets the part of the tail the formula misses; the present results suggest that in high-carry "
  "markets the drift convention should be fixed before any such adjustment is calibrated.", indent=True)
P("The Egyptian case carries a warning that reaches past the choice of measure. A supervisor who imports a one-year 99.5 percent VaR, estimates it "
  "on nominal local-currency returns and lets the closed form credit the carry will conclude that Egyptian insurers are almost riskless. The same "
  "balance sheet, with the drift stripped or the returns deflated, loses between a tenth and a sixth of its value in a 1-in-200 year, and it has done "
  "so in real terms twice since 2016. Policyholder liabilities, in life and medical business above all, are real obligations; a test that measures "
  "assets in nominal pounds against liabilities that reprice with inflation is not a solvency test. Decision 148/2025 sidesteps the problem by "
  "ignoring market risk, which is safe only while the premium-based margin happens to exceed the real loss. This is the transition hazard Windsor et "
  "al. (2024) describe in general terms, made concrete: an imported tool measures the risk of the exporting market. For Saudi Arabia the evidence is "
  "more reassuring and more specific. The sector's tail is covered by the formula under the convention insurers will apply, the 2026 parallel run is "
  "unlikely to reveal a market-risk shortfall, and where the evidence does bite is on diversification credit, which halves in the COVID and 2022 "
  "windows, and on the drift convention, which the Authority should fix explicitly rather than inherit.", indent=True)

# ================================================================== 5 CONCLUSION
H("5.  Conclusion and Policy Implications", 1)
H("5.1  Conclusion and Regulatory Implications", 2)
P(f"On RQ1, VaR and ES differ by {g_gap[0]:.1f} to {g_gap[1]:.1f} points under normality and by {b_gap[0]:.1f} to {b_gap[1]:.1f} points on the bootstrap "
  f"distributions of the mature portfolios, so most of the distance between the measures is created by the distributional assumption; the daily "
  f"backtests show that the assumption to fix is the combination of tail shape and volatility dynamics, since a filtered historical simulation "
  f"passes where every static model fails. On RQ2, the simplified standard-formula charge covers the Gaussian ES of every portfolio and, with the "
  f"drift credited, the bootstrap ES of the Saudi and nominal Egyptian portfolios, but it falls short of the bootstrap tail of the {sf_short_names} "
  f"portfolios by {sf_short_pts} points, has no answer to the real Egyptian loss of {pc(EGR['B_VaR_0.995'])} percent, and loses its Egyptian and most of "
  f"its Saudi margin once the drift is removed. On RQ3, risk-based capital in Egypt must be calibrated in the units in which liabilities fall due and "
  f"under an explicit drift convention, while Saudi Arabia's market calibration is adequate in level and needs refinement in its treatment of "
  f"diversification, its monitoring measure and the same convention.", indent=True)
P(f"For Egypt's Financial Regulatory Authority, which must write the market-risk rules that Law 155/2024 makes possible, four design choices follow. "
  f"The market module should be calibrated on real rather than nominal returns, or at least under a zero-drift convention, so that a portfolio with a "
  f"nominal Gaussian VaR of {pc(EG['G_VaR_0.995'])} percent is recognised as one that loses {pc(EG0['gauss_zero']['VaR'])} percent with the carry removed and "
  f"{pc(EGR['B_VaR_0.995'])} percent in real terms; the two routes give the same order of magnitude, and either closes the gap that Decision 148/2025 "
  f"leaves open. A currency module should treat dollar assets as a hedge rather than a risk for pound-based liabilities, since the dollar deposit is the "
  f"position that jumps in each devaluation and the reason the Egyptian diversification benefit in Table 8 holds under stress. Stress scenarios should "
  f"be anchored to the 2016 and 2022–2024 episodes. And expected shortfall should enter as a Pillar 2 monitoring measure beside VaR, because the "
  f"bootstrap ES-VaR gap of {gap(EG, 'B'):.1f} points for the nominal portfolio is the quantity that shows how much tail the premium-based margin is "
  f"silently carrying.", indent=True)
P(f"For Saudi Arabia's Insurance Authority, whose regime becomes mandatory in January 2027, three refinements follow. Insurers should report ES beside "
  f"VaR in the ORSA-equivalent, because the ES-VaR gap is where the equity-heavy outliers in a sector with a median SCR coverage of 142 percent will be "
  f"visible. Diversification credit should be calibrated on stressed correlations, since the Saudi benefit falls from {pc(ST['Saudi insurer']['full'][0])} "
  f"percent in the full sample to {pc(ST['Saudi insurer']['COVID 2020'][0])} percent in the COVID window. And the framework should state its drift "
  f"convention: with the carry credited the Solvency II-style charge exceeds the bootstrap ES by {100*cover['Saudi insurer']:.1f} points, with the carry "
  f"removed it falls {abs(100*cover0['Saudi insurer']):.1f} points short, and the Authority's own 50 percent equity stress, which implies "
  f"{pc(SA['SaudiRBC_equity50'])} percent for the sector portfolio, is not the binding constraint in either case. The calibration window should span at "
  f"least the 2020 and 2022 episodes, on which the Saudi tail in this paper entirely rests.", indent=True)
P(f"For EIOPA and the European Commission, which left the measure and the confidence level untouched in the 2025 review, the results argue against "
  f"reopening Pillar 1 and for strengthening Pillar 2. Replacing VaR with ES in Article 101 would, on Gaussian assumptions, add {g_gap[0]:.1f} to "
  f"{g_gap[1]:.1f} points and could be undone by a change of confidence level; what closes the shortfall of {sf_short_pts} points against the "
  f"bootstrap tails of the {sf_short_names} portfolios is a fat-tailed, volatility-aware distribution, and the efficient place to require it is the "
  f"ORSA (Aigner, 2025): guidance that insurers report a filtered or bootstrap ES beside the standard-formula figure and stress their diversification "
  f"on correlations of the kind in Table 8. The skewness route of Kim, Kim and Kim (2025) remains open should the Commission prefer a Pillar 1 "
  f"answer.", indent=True)
H("5.2  Limitations of the Study", 2)
P("Seven limitations apply. The analysis is asset-side only and abstracts from liabilities, underwriting risk and the asset-liability interaction a "
  "full SCR captures. The Egyptian weights are stylised, because the Authority publishes no instrument breakdown for companies; a lower deposit weight "
  "would raise the equity and currency share of the tail and move the nominal estimates toward the real ones, so the direction of the Egyptian "
  "conclusion is robust to the weight but its size is not. Several series observe a broader universe than the balance sheet they stand for: the "
  "sukuk fund is global, the Egyptian property basket is listed developers rather than direct property, and deposits accrue at the policy rate rather "
  "than at negotiated rates. The Saudi portfolio rests on six and a half years and two stress episodes. The drift convention is a choice, and the "
  "paper reports both rather than resolving it; the real-terms result does not depend on it. The historical 99.5 percent estimate has the wide "
  "interval of Table 6, and the bootstrap ES moves by one to three points with the block length. Finally, the standard-formula comparator is a "
  "simplified reconstruction without the symmetric adjustment, the concentration sub-module, fund look-through or the full interest-rate term "
  "structure, and the volatility-tracking backtests use an EWMA filter rather than a fitted GARCH process.", indent=True)
H("5.3  Future Research", 2)
P("Five testable propositions follow.", indent=True)
for t in ["**P1.** At the 99.5 percent calibration the ES–VaR gap on empirical loss distributions is at least twice the Gaussian gap, and the ratio rises with the equity weight.",
          "**P2.** The with-drift Gaussian VaR understates the zero-drift and real-terms loss by more the higher the nominal carry, so the drift convention matters most in high-inflation markets.",
          "**P3.** For insurers whose liabilities reprice with inflation, a real-terms solvency test ranks companies differently from a nominal test; Egypt's first risk-based returns under Law 155 are the natural test case.",
          "**P4.** Diversification credit on stressed correlations is lower than full-sample credit for portfolios dominated by equity and duration, but not for portfolios holding foreign-currency assets as a devaluation hedge.",
          "**P5.** A filtered historical simulation passes coverage and independence tests in emerging-market insurer portfolios where static Gaussian and Student-t models fail, and its annual aggregate approaches the block-bootstrap tail."]:
    p = P(t, after=3); p.paragraph_format.left_indent = Cm(0.75)
P("P1, P2, P4 and P5 can be tested by replicating the design on other emerging-market portfolios with a fitted GARCH filter; P3 needs supervisory data. "
  "Extending the asset-side design to a full balance sheet with inflation-linked liabilities is the natural next step for the Egyptian case.", indent=True, before=4)

# ================================================================== DECLARATIONS AND REFERENCES
_sec[0] = "other"
if not BLIND:
    H("Declarations", 1)
    P(f"**Data and code availability.** All market data are from the public sources listed in Table 1. The aligned daily dataset, the Python scripts that reproduce Tables 1–8 and Figures 1–5, the simulation outputs and the environment specification are openly available at {REPO_URL} (release v1.0.0).", after=2)
    YELLOW("Zenodo DOI: to be inserted after release", align="l", size=11, after=6)
    P("**Funding.** None.   **Conflicts of interest.** None.   **Ethics.** Not applicable; no human subjects or confidential data were used.", after=3)
    P("**Author contribution.** The author is solely responsible for the conception, analysis and writing of this article.", after=8)

H("References", 1)
refs = [
 "Acerbi, C., & Székely, B. (2014). Back-testing expected shortfall. *Risk, 27*(11), 76–81.",
 "Acerbi, C., & Tasche, D. (2002). On the coherence of expected shortfall. *Journal of Banking & Finance, 26*(7), 1487–1503. https://doi.org/10.1016/S0378-4266(02)00283-2",
 "Ahmed, M., Khalil, A., & Hassan, S. (2024). Factors influencing solvency margin of the Egyptian insurance companies. *The Academic Journal of Contemporary Commercial Research, 4*(3), 48–67. https://doi.org/10.21608/ajccr.2024.237226.1084",
 "Aigner, P. (2025). Identifying scenarios for the own risk and solvency assessment of insurance companies. *Insurance: Mathematics and Economics, 122*, 30–43. https://doi.org/10.1016/j.insmatheco.2025.01.009",
 "Alzahrani, A. (2024, May). Risk-based capital regime in the Saudi Arabia insurance market. *The Actuary Magazine*. Society of Actuaries. https://www.theactuarymagazine.org/risk-based-capital-regime-in-the-saudi-arabia-insurance-market/",
 "Artzner, P., Delbaen, F., Eber, J.-M., & Heath, D. (1999). Coherent measures of risk. *Mathematical Finance, 9*(3), 203–228. https://doi.org/10.1111/1467-9965.00068",
 "Asadi, S., & Al Janabi, M. A. M. (2020). Measuring market and credit risk under Solvency II: Evaluation of the standard technique versus internal model. *European Actuarial Journal, 10*(2), 425–456. https://doi.org/10.1007/s13385-020-00235-0",
 "Barone-Adesi, G., Giannopoulos, K., & Vosper, L. (1999). VaR without correlations for portfolios of derivative securities. *Journal of Futures Markets, 19*(5), 583–602. https://doi.org/10.1002/(SICI)1096-9934(199908)19:5<583::AID-FUT5>3.0.CO;2-S",
 "Basel Committee on Banking Supervision. (2019). *Minimum capital requirements for market risk*. Bank for International Settlements.",
 "Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics, 31*(3), 307–327. https://doi.org/10.1016/0304-4076(86)90063-1",
 "Boonen, T. J. (2017). Solvency II solvency capital requirement for life insurance companies based on expected shortfall. *European Actuarial Journal, 7*(2), 405–434. https://doi.org/10.1007/s13385-017-0160-4",
 "Braun, A., Schmeiser, H., & Schreiber, F. (2017). Portfolio optimization under Solvency II: Implicit constraints imposed by the market risk standard formula. *Journal of Risk and Insurance, 84*(1), 177–207. https://doi.org/10.1111/jori.12077",
 "Chaiyawat, T., & Guayjarernpanishk, P. (2025). Enhancing insurer portfolio resilience and capital efficiency with green bonds: A framework combining dynamic R-vine copulas and tail-risk modeling. *Risks, 13*(9), 163. https://doi.org/10.3390/risks13090163",
 "Chen, Y., Stadje, M., & Zhang, F. (2024). On the equivalence between value-at-risk- and expected shortfall-based risk measures in non-concave optimization. *Insurance: Mathematics and Economics, 117*, 114–129. https://doi.org/10.1016/j.insmatheco.2024.04.002",
 "Christiansen, M. C., & Niemeyer, A. (2014). Fundamental definition of the solvency capital requirement in Solvency II. *ASTIN Bulletin, 44*(3), 501–533. https://doi.org/10.1017/asb.2014.10",
 "Christoffersen, P. F. (1998). Evaluating interval forecasts. *International Economic Review, 39*(4), 841–862. https://doi.org/10.2307/2527341",
 "Deng, K., & Qiu, J. (2021). Backtesting expected shortfall and beyond. *Quantitative Finance, 21*(7), 1109–1125. https://doi.org/10.1080/14697688.2020.1834121",
 "Dlamini, S., & Shongwe, S. (2026). Comparative analysis of tail risk in emerging and developed equity markets: An extreme value theory perspective. *International Journal of Financial Studies, 14*(1), 11. https://doi.org/10.3390/ijfs14010011",
 "Eling, M., & Jung, K. (2020). Risk aggregation in non-life insurance: Standard models vs. internal models. *Insurance: Mathematics and Economics, 95*, 183–198. https://doi.org/10.1016/j.insmatheco.2020.09.003",
 "Eling, M., Schmeiser, H., & Schmit, J. T. (2007). The Solvency II process: Overview and critical analysis. *Risk Management and Insurance Review, 10*(1), 69–85. https://doi.org/10.1111/j.1540-6296.2007.00125.x",
 "European Commission. (2015). Commission Delegated Regulation (EU) 2015/35 supplementing Directive 2009/138/EC (Solvency II). *Official Journal of the European Union*, L 12.",
 "European Insurance and Occupational Pensions Authority. (2024). *Financial stability report, December 2024*. EIOPA.",
 "European Insurance and Occupational Pensions Authority. (2025). *Financial stability report, June 2025*. EIOPA.",
 "European Parliament & Council of the European Union. (2009). Directive 2009/138/EC on the taking-up and pursuit of the business of insurance and reinsurance (Solvency II). *Official Journal of the European Union*, L 335.",
 "European Parliament & Council of the European Union. (2025). Directive (EU) 2025/2 of 27 November 2024 amending Directive 2009/138/EC as regards proportionality, quality of supervision, reporting, long-term guarantee measures, macro-prudential tools, sustainability risks, and group and cross-border supervision. *Official Journal of the European Union*, L, 2025/2, 8 January 2025.",
 "Financial Regulatory Authority. (2025a, August 5). *FRA issues new rules for the financial solvency margin to enhance the stability of the insurance sector* (Board Decision No. 148 of 2025) [Press release]. Arab Republic of Egypt. https://fra.gov.eg",
 "Financial Regulatory Authority. (2025b, February). *Decision No. 2 of 2025 updating the investment rules for insurance and reinsurance companies*. Arab Republic of Egypt.",
 "Financial Regulatory Authority. (2026). *Annual report 2025: Insurance sector indicators* [Net investments of insurance companies about EGP 370 billion at end-2025]. Arab Republic of Egypt. https://fra.gov.eg",
 "Fissler, T., & Ziegel, J. F. (2016). Higher order elicitability and Osband's principle. *The Annals of Statistics, 44*(4), 1680–1707. https://doi.org/10.1214/16-AOS1439",
 "Gatzert, N., & Martin, M. (2012). Quantifying credit and market risk under Solvency II: Standard approach versus internal model. *Insurance: Mathematics and Economics, 51*(3), 649–666. https://doi.org/10.1016/j.insmatheco.2012.09.002",
 "Gneiting, T. (2011). Making and evaluating point forecasts. *Journal of the American Statistical Association, 106*(494), 746–762. https://doi.org/10.1198/jasa.2011.r10138",
 "Grochola, N., & Schlütter, S. (2024). Discretionary decisions in capital requirements under Solvency II. *The Geneva Papers on Risk and Insurance — Issues and Practice, 50*(2), 405–443. https://doi.org/10.1057/s41288-024-00330-3",
 "Höring, D. (2013). Will Solvency II market risk requirements bite? The impact of Solvency II on insurers' asset allocation. *The Geneva Papers on Risk and Insurance — Issues and Practice, 38*(2), 250–273. https://doi.org/10.1057/gpp.2012.31",
 "Insurance Authority. (2026a, April 5). *The Insurance Authority announces transition to the risk-based capital framework* [Press release]. Kingdom of Saudi Arabia. https://www.ia.gov.sa/en/media-center/news/104",
 "Insurance Authority. (2026b). *The Saudi insurance market report 2025*. Kingdom of Saudi Arabia. https://www.ia.gov.sa/SectorReports/",
 "J.P. Morgan & Reuters. (1996). *RiskMetrics technical document* (4th ed.). Morgan Guaranty Trust Company.",
 "Kim, H., Kim, J., & Kim, J. H. T. (2025). A new skewness adjustment for Solvency II SCR standard formula. *Scandinavian Actuarial Journal, 2025*(7), 635–658. https://doi.org/10.1080/03461238.2024.2446399",
 "Kratz, M., Lok, Y. H., & McNeil, A. J. (2018). Multinomial VaR backtests: A simple implicit approach to backtesting expected shortfall. *Journal of Banking & Finance, 88*, 393–407. https://doi.org/10.1016/j.jbankfin.2018.01.002",
 "Kupiec, P. H. (1995). Techniques for verifying the accuracy of risk measurement models. *The Journal of Derivatives, 3*(2), 73–84. https://doi.org/10.3905/jod.1995.407942",
 "Lowet, D. (2026). The Solvency II review: Key amendments and implementation challenges. *ERA Forum, 27*(1), 75–92. https://doi.org/10.1007/s12027-026-00874-y",
 "Markowitz, H. (1952). Portfolio selection. *The Journal of Finance, 7*(1), 77–91. https://doi.org/10.2307/2975974",
 "McNeil, A. J., & Frey, R. (2000). Estimation of tail-related risk measures for heteroscedastic financial time series: An extreme value approach. *Journal of Empirical Finance, 7*(3–4), 271–300. https://doi.org/10.1016/S0927-5398(00)00012-8",
 "McNeil, A. J., Frey, R., & Embrechts, P. (2015). *Quantitative risk management: Concepts, techniques and tools* (Rev. ed.). Princeton University Press.",
 "Mosa, A. (2025). The impact of investment policies on the financial solvency of insurance companies in the Kingdom of Saudi Arabia. *Journal of Financial Risk Management, 14*(4), 544–564. https://doi.org/10.4236/jfrm.2025.144029",
 "Müller-Bloch, C., & Kranz, J. (2015). A framework for rigorously identifying research gaps in qualitative literature reviews. In *Proceedings of the 36th International Conference on Information Systems (ICIS 2015)*. Association for Information Systems.",
 "Nolde, N., & Ziegel, J. F. (2017). Elicitability and backtesting: Perspectives for banking regulation. *The Annals of Applied Statistics, 11*(4), 1833–1874. https://doi.org/10.1214/17-AOAS1041",
 "Patton, A. J., Ziegel, J. F., & Chen, R. (2019). Dynamic semiparametric models for expected shortfall (and value-at-risk). *Journal of Econometrics, 211*(2), 388–413. https://doi.org/10.1016/j.jeconom.2018.10.008",
 "Pflug, G. Ch. (2000). Some remarks on the value-at-risk and the conditional value-at-risk. In S. Uryasev (Ed.), *Probabilistic constrained optimization* (pp. 272–281). Springer. https://doi.org/10.1007/978-1-4757-3150-7_15",
 "Politis, D. N., & Romano, J. P. (1994). The stationary bootstrap. *Journal of the American Statistical Association, 89*(428), 1303–1313. https://doi.org/10.1080/01621459.1994.10476870",
 "Robinson, K. A., Saldanha, I. J., & McKoy, N. A. (2011). Development of a framework to identify research gaps from systematic reviews. *Journal of Clinical Epidemiology, 64*(12), 1325–1330. https://doi.org/10.1016/j.jclinepi.2011.06.009",
 "Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. *The Journal of Risk, 2*(3), 21–41. https://doi.org/10.21314/JOR.2000.038",
 "Rockafellar, R. T., & Uryasev, S. (2002). Conditional value-at-risk for general loss distributions. *Journal of Banking & Finance, 26*(7), 1443–1471. https://doi.org/10.1016/S0378-4266(02)00271-6",
 "Shim, J., & Lee, S.-H. (2016). Dependency between risks and the insurer's economic capital: A copula-based GARCH model. *Asia-Pacific Journal of Risk and Insurance, 11*(1). https://doi.org/10.1515/apjri-2016-0021",
 "Windsor, P., Vogelsang, S., Henning, C., Martin, K., Omondi, E., Rubio, G., & Steynberg, J. (2024). *Implementing risk-based solvency for insurers: Lessons from Kenya, Mexico, and South Africa* (IMF Working Paper No. 2024/240). International Monetary Fund. https://doi.org/10.5089/9798400294631.001",
 "Yamai, Y., & Yoshiba, T. (2005). Value-at-risk versus expected shortfall: A practical perspective. *Journal of Banking & Finance, 29*(4), 997–1015. https://doi.org/10.1016/j.jbankfin.2004.08.010",
]
for ref in refs:
    p = _P0(ref, align="l", size=11, after=3); p.paragraph_format.left_indent = Cm(1.0); p.paragraph_format.first_line_indent = Cm(-1.0); p.paragraph_format.line_spacing = 1.0
name = f"{STEM}_BLINDED.docx" if BLIND else f"{STEM}.docx"
doc.save(os.path.join(VER, name)); print("saved", os.path.join(VER, name))
main = sum(_counts[k] for k in "12345")
print("WORDS", {**_counts, "main_text": main})
if not BLIND:
    json.dump({"main_text": main, "sections": {k: v for k, v in _counts.items()}}, open(f"{HERE}/wordcount.json", "w"), indent=1)
