import { useState } from "react";
import {
  useAccuracySummary,
  useAccuracyByHorizon,
  useMeta,
} from "../../api/hooks";
import { LoadingSpinner, ErrorBanner } from "../../components/States";
import { DailyAccuracyChart } from "./DailyAccuracyChart";
import { HorizonChart } from "./HorizonChart";

export function AccuracyPage() {
  const { data: meta } = useMeta();

  const [fromDate, setFromDate] = useState("2026-01-02");
  const [toDate, setToDate] = useState("2026-02-01");
  const [cutoff, setCutoff] = useState("09:00");

  const {
    data: summaryData,
    isLoading: isSummaryLoading,
    isError: isSummaryError,
    error: summaryError,
    refetch: refetchSummary,
  } = useAccuracySummary(fromDate, toDate, cutoff);

  const { data: horizonData } = useAccuracyByHorizon(fromDate, toDate);

  const m = summaryData?.overall;

  // Date range formatted label (e.g. "2 Jan – 1 Feb 2026")
  const fromD = new Date(fromDate + "T00:00:00Z");
  const toD = new Date(toDate + "T00:00:00Z");
  const rangeStr =
    !isNaN(fromD) && !isNaN(toD)
      ? `${fromD.toLocaleDateString("en-GB", { day: "numeric", month: "short", timeZone: "UTC" })} – ${toD.toLocaleDateString("en-GB", { day: "numeric", month: "short", year: "numeric", timeZone: "UTC" })}`
      : `${fromDate} – ${toDate}`;

  const biasSign = m && m.bias_mw > 0 ? "+" : "";
  const biasDirection = m && m.bias_mw >= 0 ? "above" : "below";

  return (
    <div>
      {/* Page Title */}
      <div className="page-title-block">
        <h1 className="page-title">Forecast accuracy</h1>
        <p className="page-subtitle">
          How far the decision-time forecast was from what was generated. Error
          is forecast minus actual, so a positive number means the forecast was
          too high.
        </p>
      </div>

      {/* Analysis window controls */}
      <section aria-label="Analysis window" className="settings-card">
        <div className="field-group">
          <label htmlFor="from" className="field-label">
            From delivery day
          </label>
          <input
            id="from"
            type="date"
            value={fromDate}
            min={meta?.data_window_start || "2025-12-30"}
            max={meta?.data_window_end || "2026-02-03"}
            onChange={(e) => setFromDate(e.target.value)}
            className="input-control"
          />
        </div>

        <div className="field-group">
          <label htmlFor="to" className="field-label">
            To delivery day
          </label>
          <input
            id="to"
            type="date"
            value={toDate}
            min={meta?.data_window_start || "2025-12-30"}
            max={meta?.data_window_end || "2026-02-03"}
            onChange={(e) => setToDate(e.target.value)}
            className="input-control"
          />
        </div>

        <div className="field-group">
          <label htmlFor="cutoff" className="field-label">
            Decision cutoff, day before delivery
          </label>
          <input
            id="cutoff"
            type="time"
            value={cutoff}
            onChange={(e) => setCutoff(e.target.value)}
            className="input-control"
          />
          <div className="preset-buttons">
            <button
              type="button"
              className={`preset-btn ${cutoff === "11:00" ? "preset-btn-active" : ""}`}
              onClick={() => setCutoff("11:00")}
            >
              11:00 (Auction close)
            </button>
            <button
              type="button"
              className={`preset-btn ${cutoff === "09:00" ? "preset-btn-active" : ""}`}
              onClick={() => setCutoff("09:00")}
            >
              09:00 (Morning)
            </button>
            <button
              type="button"
              className={`preset-btn ${cutoff === "16:00" ? "preset-btn-active" : ""}`}
              onClick={() => setCutoff("16:00")}
            >
              16:00 (Evening)
            </button>
          </div>
        </div>

        <p className="settings-note">
          Each delivery day is judged on the forecast you would have had at the
          cutoff the day before. Times are GMT.
        </p>
      </section>

      {/* Loading & Error States */}
      {isSummaryLoading && (
        <LoadingSpinner message="Calculating accuracy statistics..." />
      )}
      {isSummaryError && (
        <ErrorBanner error={summaryError} onRetry={refetchSummary} />
      )}

      {!isSummaryLoading && !isSummaryError && m && (
        <>
          {/* Summary metrics strip */}
          <section aria-label="Summary metrics" style={{ marginBottom: "16px" }}>
            <div className="section-header-row">
              <h2 className="section-h2">Summary, {rangeStr}</h2>
              <div className="section-meta-sub">
                {summaryData.total_evaluated_periods.toLocaleString()} half-hours
                · {summaryData.total_missing_forecasts} missing forecasts ·{" "}
                {summaryData.total_missing_actuals} missing actuals
              </div>
            </div>

            <div className="metrics-strip">
              <div className="metric-card">
                <div className="metric-label">Bias</div>
                <div className="metric-value">
                  {biasSign}
                  {Math.round(m.bias_mw).toLocaleString()}{" "}
                  <span className="metric-unit">MW</span>
                </div>
                <div className="metric-subtext">
                  Forecast {biasDirection} actual on average
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Mean absolute error</div>
                <div className="metric-value">
                  {Math.round(m.mae_mw).toLocaleString()}{" "}
                  <span className="metric-unit">MW</span>
                </div>
                <div className="metric-subtext">Typical size of the miss</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Root mean square error</div>
                <div className="metric-value">
                  {Math.round(m.rmse_mw).toLocaleString()}{" "}
                  <span className="metric-unit">MW</span>
                </div>
                <div className="metric-subtext">Weights large misses more</div>
              </div>

              <div className="metric-card">
                <div className="metric-label">90th percentile of miss</div>
                <div className="metric-value">
                  {Math.round(m.p90_abs_error_mw).toLocaleString()}{" "}
                  <span className="metric-unit">MW</span>
                </div>
                <div className="metric-subtext">
                  Nine in ten half-hours were closer than this
                </div>
              </div>

              <div className="metric-card">
                <div className="metric-label">Weighted absolute % error</div>
                <div className="metric-value">
                  {m.wape_pct !== null ? m.wape_pct.toFixed(1) : "—"}{" "}
                  <span className="metric-unit">%</span>
                </div>
                <div className="metric-subtext">
                  Total miss as a share of total actual output
                </div>
              </div>
            </div>
          </section>

          {/* Middle Row: Error by lead time (Horizon) & Error by delivery day */}
          <div className="two-col-grid">
            <HorizonChart buckets={horizonData?.buckets || []} />
            <DailyAccuracyChart
              daily={summaryData.daily || []}
              windowMae={m.mae_mw}
            />
          </div>

          {/* Bottom Row: Over-forecast risk & Definitions */}
          <div className="two-col-grid">
            <section
              aria-label="Over-forecast risk"
              className="col-left-narrow"
              style={{ display: "flex", flexDirection: "column" }}
            >
              <h2 className="section-h2" style={{ marginBottom: "12px" }}>
                Over-forecast risk
              </h2>
              <div className="risk-stat-value">
                {Math.round(m.p90_over_forecast_mw).toLocaleString()}{" "}
                <span className="metric-unit" style={{ fontSize: "16px" }}>
                  MW
                </span>
              </div>
              <p className="risk-stat-desc">
                On nine in ten half-hours, the forecast was no more than this far
                above actual. Subtracting it from a forecast gives a cautious
                planning level.
              </p>

              <div
                className="stacked-ratio-bar"
                role="img"
                aria-label={`Forecast was above actual in ${m.over_forecast_pct}% of half-hours and below in ${m.under_forecast_pct}%.`}
              >
                <div
                  className="ratio-bar-above"
                  style={{ width: `${Math.round(m.over_forecast_pct)}%` }}
                />
                <div
                  className="ratio-bar-below"
                  style={{ width: `${Math.round(m.under_forecast_pct)}%` }}
                />
              </div>

              <div className="ratio-labels">
                <span>Above actual · {Math.round(m.over_forecast_pct)}%</span>
                <span>Below actual · {Math.round(m.under_forecast_pct)}%</span>
              </div>

              <p className="risk-foot-note">
                Calculated from the {m.count.toLocaleString()} half-hours in this
                window. It describes what happened, not what will happen.
              </p>
            </section>

            <section aria-label="How to read these numbers" className="col-right-wide">
              <h2 className="section-h2" style={{ marginBottom: "14px" }}>
                How to read these numbers
              </h2>
              <dl className="definitions-grid">
                <div className="def-item">
                  <dt className="def-term">Error</dt>
                  <dd className="def-desc">
                    Forecast minus actual, in megawatts. Positive means the
                    forecast was too high, which is the risky direction when you
                    rely on wind.
                  </dd>
                </div>
                <div className="def-item">
                  <dt className="def-term">Bias</dt>
                  <dd className="def-desc">
                    The average error. Over and under misses cancel out, so it
                    shows direction, not size.
                  </dd>
                </div>
                <div className="def-item">
                  <dt className="def-term">Mean absolute error</dt>
                  <dd className="def-desc">
                    The average size of the miss, ignoring direction. The easiest
                    single number to plan around.
                  </dd>
                </div>
                <div className="def-item">
                  <dt className="def-term">Root mean square error</dt>
                  <dd className="def-desc">
                    Like the mean absolute error, but large misses count for
                    more. A big gap between the two means occasional large misses.
                  </dd>
                </div>
                <div className="def-item">
                  <dt className="def-term">90th percentile of miss</dt>
                  <dd className="def-desc">
                    The size of miss that nine in ten half-hours stayed within.
                    A guide to the bad days, not the typical one.
                  </dd>
                </div>
                <div className="def-item">
                  <dt className="def-term">Weighted absolute % error</dt>
                  <dd className="def-desc">
                    Total absolute miss divided by total actual output. It stays
                    meaningful when generation is low, unlike a per-half-hour
                    percentage.
                  </dd>
                </div>
              </dl>
            </section>
          </div>
        </>
      )}
    </div>
  );
}
