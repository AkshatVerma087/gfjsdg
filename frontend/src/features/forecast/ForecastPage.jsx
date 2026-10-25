import { useState } from "react";
import { useForecast, useMeta } from "../../api/hooks";
import { LoadingSpinner, ErrorBanner } from "../../components/States";
import { ForecastChart } from "./ForecastChart";

export function ForecastPage() {
  const { data: meta } = useMeta();

  const [deliveryDate, setDeliveryDate] = useState("2026-01-16");
  const [cutoff, setCutoff] = useState("09:00");
  const [showTable, setShowTable] = useState(false);

  const {
    data: forecastData,
    isLoading,
    isError,
    error,
    refetch,
  } = useForecast(deliveryDate, cutoff);

  // Delivery day formatting (e.g. "Fri 16 Jan 2026")
  const deliveryD = new Date(deliveryDate + "T00:00:00Z");
  const deliveryDateFormatted = !isNaN(deliveryD)
    ? deliveryD.toLocaleDateString("en-GB", {
        weekday: "short",
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      })
    : deliveryDate;

  // Day before delivery (D-1) for cutoff label
  const dMinus1 = new Date(deliveryDate + "T00:00:00Z");
  dMinus1.setUTCDate(dMinus1.getUTCDate() - 1);
  const dMinus1Formatted = !isNaN(dMinus1)
    ? dMinus1.toLocaleDateString("en-GB", {
        weekday: "short",
        day: "numeric",
        month: "short",
        year: "numeric",
        timeZone: "UTC",
      })
    : "";

  // Summary statistics computation from 48 settlement points
  const points = forecastData?.points || [];
  const validForecasts = points.filter((p) => p.forecast_mw !== null);
  const validPairs = points.filter(
    (p) => p.forecast_mw !== null && p.actual_mw !== null
  );

  // Latest publish time used
  let latestPublishDate = null;
  points.forEach((p) => {
    if (p.publish_time) {
      const pub = new Date(p.publish_time);
      if (!latestPublishDate || pub > latestPublishDate) {
        latestPublishDate = pub;
      }
    }
  });

  const latestPublishStr = latestPublishDate
    ? latestPublishDate.toLocaleDateString("en-GB", {
        timeZone: "UTC",
        weekday: "short",
        day: "numeric",
        month: "short",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";

  // Average forecast
  const avgForecast =
    validForecasts.length > 0
      ? Math.round(
          validForecasts.reduce((acc, p) => acc + p.forecast_mw, 0) /
            validForecasts.length
        )
      : 0;

  // Lowest half-hour forecast
  let lowestHalfHour = null;
  validForecasts.forEach((p) => {
    if (!lowestHalfHour || p.forecast_mw < lowestHalfHour.forecast_mw) {
      lowestHalfHour = p;
    }
  });

  const lowestTimeStr = lowestHalfHour
    ? new Date(lowestHalfHour.start_time).toLocaleTimeString("en-GB", {
        timeZone: "UTC",
        hour: "2-digit",
        minute: "2-digit",
      })
    : "—";

  // Average miss and bias
  let sumAbsError = 0;
  let sumBias = 0;
  validPairs.forEach((p) => {
    const diff = p.forecast_mw - p.actual_mw;
    sumAbsError += Math.abs(diff);
    sumBias += diff;
  });

  const dayMae =
    validPairs.length > 0 ? Math.round(sumAbsError / validPairs.length) : 0;
  const dayBias =
    validPairs.length > 0 ? Math.round(sumBias / validPairs.length) : 0;
  const biasDirection = dayBias >= 0 ? "above" : "below";

  return (
    <div>
      {/* Title block */}
      <div className="page-title-block">
        <h1 className="page-title">Wind forecast at decision time</h1>
        <p className="page-subtitle">
          For each half-hour of the delivery day, the latest forecast that had
          been published by your cutoff on the day before, shown against what was
          actually generated.
        </p>
      </div>

      {/* Decision settings */}
      <section aria-label="Decision settings" className="settings-card">
        <div className="field-group">
          <label htmlFor="delivery" className="field-label">
            Delivery day
          </label>
          <input
            id="delivery"
            type="date"
            value={deliveryDate}
            min={meta?.data_window_start || "2025-12-30"}
            max={meta?.data_window_end || "2026-02-03"}
            onChange={(e) => setDeliveryDate(e.target.value)}
            className="input-control"
          />
        </div>

        <div className="field-group">
          <label htmlFor="cutoff" className="field-label">
            Decision cutoff, day before delivery
          </label>
          <div className="input-inline-wrap">
            <input
              id="cutoff"
              type="time"
              value={cutoff}
              onChange={(e) => setCutoff(e.target.value)}
              className="input-control"
            />
            {dMinus1Formatted && (
              <span className="inline-context-text">on {dMinus1Formatted}</span>
            )}
          </div>
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
          Move the cutoff earlier to see what you would have known if you had
          decided sooner. Times are GMT.
        </p>
      </section>

      {/* Summary strip */}
      <section aria-label="Summary" className="metrics-strip">
        <div className="metric-card">
          <div className="metric-label">Forecast used</div>
          <div className="metric-value" style={{ fontSize: "22px" }}>
            {latestPublishStr}
          </div>
          <div className="metric-subtext">
            Latest publish at or before {cutoff}
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Average forecast</div>
          <div className="metric-value">
            {avgForecast.toLocaleString()}{" "}
            <span className="metric-unit">MW</span>
          </div>
          <div className="metric-subtext">Across 48 half-hours</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Lowest half-hour</div>
          <div className="metric-value">
            {lowestHalfHour
              ? lowestHalfHour.forecast_mw.toLocaleString()
              : "—"}{" "}
            <span className="metric-unit">MW</span>
          </div>
          <div className="metric-subtext">at {lowestTimeStr}</div>
        </div>

        <div className="metric-card">
          <div className="metric-label">Average miss, this day</div>
          <div className="metric-value">
            {dayMae.toLocaleString()} <span className="metric-unit">MW</span>
          </div>
          <div className="metric-subtext">
            Forecast ran {Math.abs(dayBias).toLocaleString()} MW {biasDirection}{" "}
            actual on average
          </div>
        </div>
      </section>

      {/* Main interactive chart / loading / error states */}
      {isLoading && <LoadingSpinner message="Loading half-hourly wind profile..." />}
      {isError && <ErrorBanner error={error} onRetry={refetch} />}

      {!isLoading && !isError && (
        <>
          <ForecastChart
            points={points}
            deliveryDateStr={deliveryDateFormatted}
            missingForecastCount={forecastData?.missing_forecast_count || 0}
            missingActualCount={forecastData?.missing_actual_count || 0}
          />

          {/* Collapsible Inspection Table */}
          <div className="table-toggle-bar">
            <button
              type="button"
              className="table-toggle-btn"
              onClick={() => setShowTable((prev) => !prev)}
            >
              {showTable ? "Hide half-hour data table ▲" : "Show all 48 half-hours in table ▼"}
            </button>
            <span style={{ fontSize: "12px", color: "#596A76" }}>
              48 settlement periods · 30-min resolution
            </span>
          </div>

          {showTable && (
            <div className="data-table-container">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Period</th>
                    <th>Start Time (GMT)</th>
                    <th>As-of Forecast</th>
                    <th>Actual Generation</th>
                    <th>Error (F − A)</th>
                    <th>Published At</th>
                    <th>Lead Time</th>
                  </tr>
                </thead>
                <tbody>
                  {points.map((p) => {
                    const time = new Date(p.start_time).toLocaleTimeString(
                      "en-GB",
                      { hour: "2-digit", minute: "2-digit", timeZone: "UTC" }
                    );
                    const diff =
                      p.forecast_mw !== null && p.actual_mw !== null
                        ? p.forecast_mw - p.actual_mw
                        : null;
                    const pub = p.publish_time
                      ? new Date(p.publish_time).toLocaleTimeString("en-GB", {
                          hour: "2-digit",
                          minute: "2-digit",
                          timeZone: "UTC",
                        })
                      : "—";

                    return (
                      <tr key={p.settlement_period}>
                        <td>{p.settlement_period}</td>
                        <td>{time}</td>
                        <td style={{ color: "#1F5FBF", fontWeight: 600 }}>
                          {p.forecast_mw !== null
                            ? `${p.forecast_mw.toLocaleString()} MW`
                            : "—"}
                        </td>
                        <td style={{ color: "#101C24", fontWeight: 600 }}>
                          {p.actual_mw !== null
                            ? `${p.actual_mw.toLocaleString()} MW`
                            : "—"}
                        </td>
                        <td
                          style={{
                            fontWeight: 600,
                            color:
                              diff > 0
                                ? "#D9731A"
                                : diff < 0
                                  ? "#1F5FBF"
                                  : "#596A76",
                          }}
                        >
                          {diff !== null
                            ? `${diff > 0 ? "+" : ""}${diff.toLocaleString()} MW`
                            : "—"}
                        </td>
                        <td>{pub}</td>
                        <td>
                          {p.lead_time_hours !== null
                            ? `${p.lead_time_hours}h`
                            : "—"}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
}
