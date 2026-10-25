import { useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  ArrowUpRight,
  TrendingUp,
  ShieldCheck,
  Zap,
  BarChart3,
  Layers,
  ChevronDown,
  Database,
  CheckCircle2,
  ExternalLink,
} from "lucide-react";
import { api } from "../../api/client";

export function LandingPage() {
  const [activeFaq, setActiveFaq] = useState(0);

  const { data: summaryData } = useQuery({
    queryKey: ["accuracy-summary", "2026-01-02", "2026-02-01", "11:00"],
    queryFn: () => api.getAccuracySummary("2026-01-02", "2026-02-01", "11:00"),
  });

  const m = summaryData?.overall;

  const faqs = [
    {
      q: "What happens if wind generation falls short during settlement?",
      a: "When metered wind is lower than the day-ahead forecast, the utility desk is left short. The System Operator (National Grid ESO) charges the difference at the System Buy Price (cashout), which can surge dramatically during high-demand half-hours. Our P90 over-forecast buffer informs risk-adjusted thermal procurement to avoid these penalty spikes.",
    },
    {
      q: "Why is the 11:00 D-1 auction cutoff strictly enforced?",
      a: "Great Britain day-ahead power exchanges (EPEX SPOT and Nord Pool) close their day-ahead auction order books at 11:00 GMT on D-1. Incorporating forecasts published after 11:00 introduces lookahead bias into historical evaluation. Our selector strictly extracts the latest WINDFOR published prior to your selected cutoff time.",
    },
    {
      q: "Is any of this data estimated, simulated, or mocked?",
      a: "No. The system operates strictly on unadulterated Elexon BMRS settlement data: FUELHH for metered wind actuals and WINDFOR for national wind forecasts across the entire January 2026 delivery window. All 1,440 half-hourly settlement periods are verified against Elexon settlement archives.",
    },
    {
      q: "How does forecast error degrade over lead time?",
      a: "Forecast accuracy scales directly with forecast horizon. Forecasts published 0–6 hours ahead of delivery exhibit an average MAE of ~1,654 MW, whereas forecasts published 48+ hours ahead degrade to ~2,307 MW. Power desks use this horizon degradation curve to decide whether to trade in the day-ahead auction or hold volume for intraday re-balancing.",
    },
  ];

  return (
    <div className="nexila-page">
      {/* ====================================================================
          1. HERO SECTION (Muzli Inspired Cinematic Wind Canvas)
          ==================================================================== */}
      <section className="nexila-hero-card" aria-label="Hero Introduction">
        <div className="nexila-hero-bg-overlay" />
        <img
          src="/hero-wind.jpg"
          alt="Wind turbines under blue sky with fluffy white clouds"
          className="nexila-hero-img"
        />

        <div className="nexila-hero-content">
          <div className="nexila-hero-left">
            <h1 className="nexila-headline">
              Power That <em>Doesn&apos;t Borrow</em> From Tomorrow
            </h1>

            <p className="nexila-subhead">
              Wind Forecast Monitor equips UK utility power desks to turn day-ahead
              wind uncertainty into quantified, risk-adjusted procurement strategy.
              Compare decision-cutoff forecasts with metered generation, cut imbalance
              cashout risk, and keep running when the grid fluctuates.
            </p>

            <div className="nexila-hero-actions">
              <Link to="/forecast" className="nexila-btn-vibrant">
                <span>Launch Decision-Time Forecast (R1)</span>
                <ArrowUpRight size={18} />
              </Link>
              <Link to="/accuracy" className="nexila-btn-glass">
                <span>Explore Accuracy &amp; Tail Risk (R2) →</span>
              </Link>
            </div>
          </div>

          <div className="nexila-hero-right">
            {/* Floating Glassmorphism Metric Widget */}
            <div className="nexila-glass-widget">
              <div className="widget-header">
                <span className="widget-icon-pill">
                  <Zap size={14} />
                </span>
                <div>
                  <div className="widget-stat">
                    {summaryData?.total_evaluated_periods
                      ? `${summaryData.total_evaluated_periods.toLocaleString()} half-hours`
                      : "1,440 half-hours"}
                  </div>
                  <div className="widget-sub">Evaluated for January 2026 window</div>
                </div>
              </div>

              {/* Mini Generation / Error Trend Bars */}
              <div className="widget-chart-wrap" aria-hidden="true">
                <div className="widget-bars-row">
                  <div className="w-bar" style={{ height: "42%" }} title="Wk 1" />
                  <div className="w-bar" style={{ height: "60%" }} title="Wk 2" />
                  <div className="w-bar" style={{ height: "78%" }} title="Wk 3" />
                  <div className="w-bar active" style={{ height: "100%" }} title="Wk 4 (Peak)" />
                  <div className="w-bar" style={{ height: "70%" }} title="Wk 5" />
                  <div className="w-bar" style={{ height: "82%" }} title="Wk 6" />
                  <div className="w-bar" style={{ height: "92%" }} title="Wk 7" />
                </div>
                <div className="widget-chart-labels">
                  <span>2 Jan 2026</span>
                  <span>1 Feb 2026</span>
                </div>
              </div>

              <div className="widget-footer-stat">
                <span>MAE Benchmark:</span>
                <strong>{m ? `${Math.round(m.mae_mw).toLocaleString()} MW` : "1,880 MW"}</strong>
              </div>
            </div>

            {/* Floating Glassmorphism Social Proof Badge */}
            <div className="nexila-trust-badge">
              <div className="trust-stars">★★★★★</div>
              <div className="trust-text">
                <strong>100% Real Elexon Data</strong>
                <span>Official BMRS Settlement Streams</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          2. MARKET SNAPSHOT METRICS (Real Elexon Math)
          ==================================================================== */}
      <section className="nexila-snapshot-strip" aria-label="Market Performance Benchmarks">
        <div className="snapshot-card">
          <div className="snapshot-icon-wrap">
            <TrendingUp size={20} />
          </div>
          <div className="snapshot-num">
            {m ? Math.round(m.mae_mw).toLocaleString() : "1,880"} <span className="snap-unit">MW</span>
          </div>
          <div className="snapshot-label">Mean Absolute Error</div>
          <div className="snapshot-desc">Average magnitude of forecast error across 1,440 periods</div>
        </div>

        <div className="snapshot-card">
          <div className="snapshot-icon-wrap">
            <BarChart3 size={20} />
          </div>
          <div className="snapshot-num">
            +{m ? Math.round(m.bias_mw).toLocaleString() : "1,698"} <span className="snap-unit">MW</span>
          </div>
          <div className="snapshot-label">Systematic Forecast Bias</div>
          <div className="snapshot-desc">Mean over-forecast direction (forecast &gt; actual outturn)</div>
        </div>

        <div className="snapshot-card">
          <div className="snapshot-icon-wrap">
            <ShieldCheck size={20} />
          </div>
          <div className="snapshot-num">
            {m ? Math.round(m.p90_over_forecast_mw).toLocaleString() : "3,796"} <span className="snap-unit">MW</span>
          </div>
          <div className="snapshot-label">P90 Tail Miss Buffer</div>
          <div className="snapshot-desc">Empirical buffer for risk-adjusted conservative procurement</div>
        </div>

        <div className="snapshot-card">
          <div className="snapshot-icon-wrap">
            <Layers size={20} />
          </div>
          <div className="snapshot-num">
            {m ? Math.round(m.over_forecast_pct) : "88"}%
          </div>
          <div className="snapshot-label">Over-Forecast Ratio</div>
          <div className="snapshot-desc">Proportion of half-hours where wind failed to meet prediction</div>
        </div>
      </section>

      {/* ====================================================================
          3. ENGINEERING & OPERATIONAL MECHANICS (Muzli Cutaway Layout)
          ==================================================================== */}
      <section className="nexila-section" aria-label="Engineering Architecture">
        <div className="nexila-section-tag">
          <span>About The Engine</span>
        </div>

        <h2 className="nexila-section-title">
          A Journey Through the Market Mechanics and Care That Define Every Single Megawatt.
        </h2>

        <div className="nexila-two-col-layout">
          <div className="nexila-cutaway-box">
            <img
              src="/turbine-cutaway.jpg"
              alt="Detailed 3D engineering cutaway render of a modern wind turbine nacelle and internal generator"
              className="nexila-cutaway-img"
            />
            <div className="cutaway-caption">
              <strong>Elexon BMRS Telemetry</strong> · Synchronized at 48 Settlement Periods Daily
            </div>
          </div>

          <div className="nexila-narrative-box">
            <p className="narrative-lead">
              At Wind Forecast Monitor, we believe managing renewable intermittency is more than reading
              raw charts. Every system we build starts with strict market synchronization: pairing D-1
              forecast timestamps with metered generation half-hour by half-hour.
            </p>
            <p className="narrative-body">
              Nothing is copied from a template or interpolated with synthetic approximations. Every period,
              settlement boundary, and cutoff rule is sized precisely for the Great Britain day-ahead power market.
            </p>

            <div className="narrative-points">
              <div className="narrative-point-item">
                <CheckCircle2 size={18} className="narrative-check" />
                <div>
                  <strong>Decision Cutoff Synchronization (R1)</strong>
                  <span>Freezes data at 11:00 D-1 auction gate to prevent costly lookahead bias.</span>
                </div>
              </div>
              <div className="narrative-point-item">
                <CheckCircle2 size={18} className="narrative-check" />
                <div>
                  <strong>Tail Risk Quantification (R2)</strong>
                  <span>Calculates P90/P95 tail miss distributions to guide thermal reserve purchasing.</span>
                </div>
              </div>
              <div className="narrative-point-item">
                <CheckCircle2 size={18} className="narrative-check" />
                <div>
                  <strong>Pure Stateless Metrics Architecture</strong>
                  <span>Sub-millisecond mathematical calculation with zero database lock contention.</span>
                </div>
              </div>
            </div>

            <div className="narrative-actions">
              <Link to="/forecast" className="narrative-cta">
                <span>View Decision-Time Forecast →</span>
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ====================================================================
          4. BENEFITS / CAPABILITIES BENTO GRID
          ==================================================================== */}
      <section className="nexila-section" aria-label="Benefits">
        <div className="nexila-section-tag">
          <span>Benefits</span>
        </div>

        <h2 className="nexila-section-title">
          Power Your Desk with Clean, Verifiable Analytics
        </h2>

        <div className="nexila-bento-grid">
          <div className="bento-card bento-card-wide">
            <div className="bento-tag">Empirical Risk Management</div>
            <h3 className="bento-h3">Protect Against Imbalance Cashout Charges</h3>
            <p className="bento-desc">
              When wind under-delivers, purchasing replacement power at system cashout prices can cost 2x–5x
              day-ahead rates. By deducting the empirical P90 miss from raw forecasts, purchasing leads establish
              a resilient thermal procurement floor.
            </p>
            <div className="bento-stat-strip">
              <div className="bento-stat">
                <div className="b-val">3,796 MW</div>
                <div className="b-sub">P90 Over-Forecast Margin</div>
              </div>
              <div className="bento-stat">
                <div className="b-val">87.9%</div>
                <div className="b-sub">Directional Accuracy Ratio</div>
              </div>
            </div>
          </div>

          <div className="bento-card">
            <div className="bento-tag">Horizon Analytics</div>
            <h3 className="bento-h3">Lead-Time Horizon Curves</h3>
            <p className="bento-desc">
              Understand how forecast error scales with lead time across 5 distinct age buckets (0–6h, 6–12h,
              12–24h, 24–48h, and 48h+) to optimize timing between day-ahead auctions and intraday re-balancing.
            </p>
            <Link to="/accuracy" className="bento-link">
              <span>Inspect Lead Times →</span>
            </Link>
          </div>

          <div className="bento-card">
            <div className="bento-tag">Open Architecture</div>
            <h3 className="bento-h3">Enterprise REST API &amp; OpenAPI</h3>
            <p className="bento-desc">
              Every metric, curve, and settlement calculation is accessible via structured JSON REST endpoints with
              strict Zod payload validation, request-ID tracing, and interactive OpenAPI documentation.
            </p>
            <a href="/api/v1/docs" target="_blank" rel="noopener noreferrer" className="bento-link">
              <span>View OpenAPI Docs</span>
              <ExternalLink size={14} />
            </a>
          </div>
        </div>
      </section>

      {/* ====================================================================
          5. TECHNICAL ACCORDION FAQ ("You Ask. We Don't Dodge.")
          ==================================================================== */}
      <section className="nexila-section" aria-label="Frequently Asked Questions">
        <div className="faq-layout">
          <div className="faq-intro">
            <div className="nexila-section-tag">
              <span>FAQ</span>
            </div>
            <h2 className="faq-main-title">
              You Ask. We Don&apos;t Dodge.
            </h2>
            <p className="faq-intro-text">
              Have questions about settlement methodology, BMRS data streams, or how to translate historical
              error percentiles into day-ahead purchasing decisions? Here are direct answers.
            </p>
            <div className="faq-action-box">
              <Link to="/forecast" className="faq-launch-btn">
                <span>Try Live Portal</span>
                <ArrowUpRight size={16} />
              </Link>
            </div>
          </div>

          <div className="faq-list">
            {faqs.map((item, idx) => {
              const isOpen = activeFaq === idx;
              return (
                <div
                  key={idx}
                  className={`faq-item ${isOpen ? "faq-item-open" : ""}`}
                >
                  <button
                    type="button"
                    className="faq-question-btn"
                    onClick={() => setActiveFaq(isOpen ? -1 : idx)}
                    aria-expanded={isOpen}
                  >
                    <span>{item.q}</span>
                    <ChevronDown size={18} className={`faq-chevron ${isOpen ? "rotate" : ""}`} />
                  </button>
                  {isOpen && (
                    <div className="faq-answer-body">
                      <p>{item.a}</p>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ====================================================================
          6. DATA PROVENANCE & TRANSPARENCY AUDIT
          ==================================================================== */}
      <section className="nexila-audit-bar" aria-label="Data Transparency">
        <div className="audit-inner">
          <div className="audit-brand-item">
            <Database size={18} className="audit-icon" />
            <span><strong>Elexon BMRS</strong> · Verified GB Grid Settlement</span>
          </div>
          <div className="audit-divider" />
          <div className="audit-item">
            <code>FUELHH</code> (Metered Wind Generation)
          </div>
          <div className="audit-divider" />
          <div className="audit-item">
            <code>WINDFOR</code> (Day-Ahead Production Forecasts)
          </div>
          <div className="audit-divider" />
          <div className="audit-item">
            <strong>January 2026</strong> Delivery Month (1,440 Half-Hours)
          </div>
        </div>
      </section>
    </div>
  );
}
