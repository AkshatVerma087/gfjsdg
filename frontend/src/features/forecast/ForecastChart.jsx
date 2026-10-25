import { useState, useRef } from "react";

export function ForecastChart({
  points = [],
  deliveryDateStr = "",
  missingForecastCount = 0,
  missingActualCount = 0,
}) {
  const svgRef = useRef(null);

  // 1. Pinned tooltip: Find highest forecast point index
  const highestForecastIdx = points.reduce((bestIdx, p, idx) => {
    if (p.forecast_mw === null) return bestIdx;
    if (bestIdx === -1) return idx;
    return p.forecast_mw > (points[bestIdx]?.forecast_mw ?? -Infinity) ? idx : bestIdx;
  }, -1);

  const [activeIdx, setActiveIdx] = useState(null);
  const currentIdx =
    activeIdx !== null
      ? activeIdx
      : highestForecastIdx !== -1
        ? highestForecastIdx
        : 20;

  // 2. Calculate Y scale bounds dynamically (rounded round numbers, step of 1,000)
  const validVals = [];
  points.forEach((p) => {
    if (p.forecast_mw !== null) validVals.push(p.forecast_mw);
    if (p.actual_mw !== null) validVals.push(p.actual_mw);
  });

  const rawMin = validVals.length > 0 ? Math.min(...validVals) : 5000;
  const rawMax = validVals.length > 0 ? Math.max(...validVals) : 10000;

  const step = 1000;
  const yMin = Math.max(0, Math.floor(rawMin / step) * step);
  const yMax = Math.max(yMin + 2000, Math.ceil(rawMax / step) * step);
  const numSteps = Math.max(2, Math.round((yMax - yMin) / step));

  const xLeft = 64;
  const xRight = 960;
  const yTop = 24;
  const yBottom = 304;

  const getX = (idx) => {
    if (points.length <= 1) return xLeft;
    return xLeft + (idx / (points.length - 1)) * (xRight - xLeft);
  };

  const getY = (val) => {
    if (val === null || val === undefined) return yBottom;
    const clamped = Math.max(yMin, Math.min(yMax, val));
    return yBottom - ((clamped - yMin) / (yMax - yMin)) * (yBottom - yTop);
  };

  // Horizontal Grid lines (no vertical lines)
  const gridLines = [];
  for (let i = 0; i <= numSteps; i++) {
    const val = yMax - i * ((yMax - yMin) / numSteps);
    const y = yTop + i * ((yBottom - yTop) / numSteps);
    gridLines.push({ val: Math.round(val), y });
  }

  // 3. Build curve polylines with gaps for missing data (never interpolate)
  const actualSegments = [];
  let curActSeg = [];
  points.forEach((p, idx) => {
    if (p.actual_mw !== null) {
      curActSeg.push(`${getX(idx).toFixed(1)},${getY(p.actual_mw).toFixed(1)}`);
    } else {
      if (curActSeg.length > 0) actualSegments.push(curActSeg);
      curActSeg = [];
    }
  });
  if (curActSeg.length > 0) actualSegments.push(curActSeg);

  const forecastSegments = [];
  let curFcSeg = [];
  points.forEach((p, idx) => {
    if (p.forecast_mw !== null) {
      curFcSeg.push(`${getX(idx).toFixed(1)},${getY(p.forecast_mw).toFixed(1)}`);
    } else {
      if (curFcSeg.length > 0) forecastSegments.push(curFcSeg);
      curFcSeg = [];
    }
  });
  if (curFcSeg.length > 0) forecastSegments.push(curFcSeg);

  // 4. Shading: fill ONLY the gap between the two lines
  // Orange (22% opacity) where forecast > actual, Blue (14% opacity) where forecast < actual
  const overPolygons = [];
  const underPolygons = [];

  let currentType = null;
  let currentSegment = [];

  points.forEach((p, idx) => {
    if (p.forecast_mw !== null && p.actual_mw !== null) {
      const type = p.forecast_mw >= p.actual_mw ? "over" : "under";
      if (type !== currentType) {
        if (currentSegment.length > 1) {
          if (currentType === "over") overPolygons.push([...currentSegment]);
          else underPolygons.push([...currentSegment]);
        }
        currentType = type;
        currentSegment = [];
      }
      currentSegment.push({
        idx,
        x: getX(idx),
        fY: getY(p.forecast_mw),
        aY: getY(p.actual_mw),
      });
    } else {
      if (currentSegment.length > 1) {
        if (currentType === "over") overPolygons.push([...currentSegment]);
        else underPolygons.push([...currentSegment]);
      }
      currentType = null;
      currentSegment = [];
    }
  });
  if (currentSegment.length > 1) {
    if (currentType === "over") overPolygons.push([...currentSegment]);
    else underPolygons.push([...currentSegment]);
  }

  const makePolygonPoints = (seg) => {
    const top = seg.map((pt) => `${pt.x.toFixed(1)},${pt.fY.toFixed(1)}`);
    const bottom = [...seg].reverse().map((pt) => `${pt.x.toFixed(1)},${pt.aY.toFixed(1)}`);
    return [...top, ...bottom].join(" ");
  };

  // 5. Interactions: Mouse hover & Keyboard navigation
  const handleMouseMove = (e) => {
    if (!svgRef.current || points.length === 0) return;
    const rect = svgRef.current.getBoundingClientRect();
    const mouseX = e.clientX - rect.left;
    const scale = 1000 / rect.width;
    const svgX = mouseX * scale;

    const clampedX = Math.max(xLeft, Math.min(xRight, svgX));
    const rawIdx = Math.round(((clampedX - xLeft) / (xRight - xLeft)) * (points.length - 1));
    const idx = Math.max(0, Math.min(points.length - 1, rawIdx));
    setActiveIdx(idx);
  };

  const handleMouseLeave = () => {
    setActiveIdx(null); // returns to pinned highest forecast point
  };

  const handleKeyDown = (e) => {
    if (e.key === "ArrowLeft") {
      e.preventDefault();
      setActiveIdx((prev) => {
        const c = prev !== null ? prev : currentIdx;
        return Math.max(0, c - 1);
      });
    } else if (e.key === "ArrowRight") {
      e.preventDefault();
      setActiveIdx((prev) => {
        const c = prev !== null ? prev : currentIdx;
        return Math.min(points.length - 1, c + 1);
      });
    }
  };

  // 6. Active Point Inspection Tooltip
  const activePt = points[currentIdx] || points[0];
  const activeX = activePt ? getX(currentIdx) : xLeft;
  const activeFcY = activePt && activePt.forecast_mw !== null ? getY(activePt.forecast_mw) : null;
  const activeActY = activePt && activePt.actual_mw !== null ? getY(activePt.actual_mw) : null;

  let tooltipBoxX = activeX + 16;
  if (tooltipBoxX + 262 > 980) {
    tooltipBoxX = activeX - 278;
  }
  const tooltipBoxY = 26;

  const activeTimeStr = activePt
    ? new Date(activePt.start_time).toLocaleTimeString("en-GB", {
        hour: "2-digit",
        minute: "2-digit",
        timeZone: "UTC",
      })
    : "—";

  const activeError =
    activePt && activePt.forecast_mw !== null && activePt.actual_mw !== null
      ? activePt.forecast_mw - activePt.actual_mw
      : null;

  // Use real unicode minus sign "−" for negative numbers
  const formattedErrorSign =
    activeError !== null
      ? activeError > 0
        ? `+${Math.round(activeError).toLocaleString()}`
        : activeError < 0
          ? `−${Math.abs(Math.round(activeError)).toLocaleString()}`
          : "0"
      : null;

  // Curve label positions (directly on the lines, above and below)
  const fcLabelIdx = Math.min(10, Math.floor(points.length * 0.25));
  const fcLabelPt = points[fcLabelIdx];
  const fcLabelX = fcLabelPt ? getX(fcLabelIdx) : 228;
  const fcLabelY = fcLabelPt && fcLabelPt.forecast_mw !== null ? getY(fcLabelPt.forecast_mw) - 10 : 164;
  const actLabelY = fcLabelPt && fcLabelPt.actual_mw !== null ? getY(fcLabelPt.actual_mw) + 20 : 192;

  // Visually hidden summary for accessibility
  const peakForecast = points.reduce(
    (max, p) => (p.forecast_mw !== null && p.forecast_mw > max ? p.forecast_mw : max),
    0
  );
  const lowestForecast = points.reduce(
    (min, p) =>
      p.forecast_mw !== null && (min === 0 || p.forecast_mw < min) ? p.forecast_mw : min,
    0
  );

  return (
    <section aria-label="Forecast versus actual" className="chart-card">
      {/* Visually hidden screen-reader summary */}
      <div className="sr-only">
        Wind forecast vs actual for {deliveryDateStr}. Peak forecast {peakForecast.toLocaleString()} MW,
        lowest forecast {lowestForecast.toLocaleString()} MW. {missingForecastCount} missing forecasts,{" "}
        {missingActualCount} missing actuals. Use left and right arrow keys to inspect half-hours.
      </div>

      {/* Live Region for active point announcement */}
      <div className="sr-only" aria-live="polite">
        {activePt
          ? `${deliveryDateStr} ${activeTimeStr}: Forecast ${
              activePt.forecast_mw !== null ? activePt.forecast_mw.toLocaleString() : "missing"
            } MW, Actual ${
              activePt.actual_mw !== null ? activePt.actual_mw.toLocaleString() : "missing"
            } MW${formattedErrorSign ? `, error ${formattedErrorSign} MW` : ""}`
          : ""}
      </div>

      <div className="chart-header-row">
        <div className="chart-title-block">
          <h2>Forecast vs actual, {deliveryDateStr}</h2>
          <div className="chart-subtitle">Megawatts, per half-hour, GMT</div>
        </div>

        <div className="legend-row">
          <span className="legend-item">
            <svg width="20" height="4" aria-hidden="true">
              <rect width="20" height="4" rx="2" fill="var(--chart-forecast-line)" />
            </svg>
            Forecast
          </span>
          <span className="legend-item">
            <svg width="20" height="4" aria-hidden="true">
              <rect width="20" height="4" rx="2" fill="var(--chart-actual-line)" />
            </svg>
            Actual
          </span>
          <span className="legend-item">
            <svg width="14" height="14" aria-hidden="true">
              <rect
                width="14"
                height="14"
                rx="3"
                fill="var(--chart-over-forecast)"
                fillOpacity="var(--chart-over-opacity, 0.22)"
              />
            </svg>
            Forecast above actual
          </span>
          <span className="legend-item">
            <svg width="14" height="14" aria-hidden="true">
              <rect
                width="14"
                height="14"
                rx="3"
                fill="var(--chart-forecast-line)"
                fillOpacity="var(--chart-under-opacity, 0.14)"
              />
            </svg>
            Forecast below actual
          </span>
        </div>
      </div>

      {/* Responsive scroll wrapper (scrolls horizontally below 720px) */}
      <div
        className="chart-scroll-wrapper"
        tabIndex={0}
        role="region"
        aria-label="Interactive forecast vs actual chart. Use arrow keys to inspect data points."
        onKeyDown={handleKeyDown}
      >
        <svg
          ref={svgRef}
          viewBox="0 0 1000 360"
          role="img"
          aria-label={`Line chart of wind forecast and actual generation for ${deliveryDateStr}`}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          style={{
            display: "block",
            width: "100%",
            minWidth: "720px",
            height: "auto",
            fontFamily: "var(--font-family)",
            fontVariantNumeric: "tabular-nums",
            cursor: "crosshair",
            userSelect: "none",
          }}
        >
          {/* Horizontal Grid lines only (1px, no vertical gridlines) */}
          <g stroke="var(--chart-gridlines)" strokeWidth="1">
            {gridLines.slice(0, -1).map((gl, i) => (
              <line key={i} x1={xLeft} y1={gl.y} x2={xRight} y2={gl.y} />
            ))}
          </g>

          {/* Baseline 1px in axis color */}
          <line
            x1={xLeft}
            y1={yBottom}
            x2={xRight}
            y2={yBottom}
            stroke="var(--chart-axis-line)"
            strokeWidth="1"
          />

          {/* Y Axis Labels (12px, tabular-nums, right-aligned at x=54) */}
          <g fontSize="12" fill="var(--chart-text)" textAnchor="end">
            {gridLines.map((gl, i) => (
              <text key={i} x={54} y={gl.y + 4}>
                {gl.val.toLocaleString()}
              </text>
            ))}
          </g>

          {/* X Axis Time Labels (every 4h: 00:00, 04:00 ... 20:00 plus 23:30) */}
          <g fontSize="12" fill="var(--chart-text)" textAnchor="middle">
            <text x="64" y="326">00:00</text>
            <text x="216.5" y="326">04:00</text>
            <text x="369" y="326">08:00</text>
            <text x="521.5" y="326">12:00</text>
            <text x="674" y="326">16:00</text>
            <text x="826.5" y="326">20:00</text>
            <text x="960" y="326">23:30</text>
          </g>
          <text
            x="512"
            y="350"
            fontSize="12"
            fill="var(--chart-text)"
            textAnchor="middle"
          >
            Half-hour start, GMT
          </text>

          {/* Shaded Area: Forecast > Actual (Orange at calibrated opacity) */}
          {overPolygons.map((seg, i) => (
            <polygon
              key={`over-${i}`}
              fill="var(--chart-over-forecast)"
              fillOpacity="var(--chart-over-opacity, 0.22)"
              points={makePolygonPoints(seg)}
            />
          ))}

          {/* Shaded Area: Forecast < Actual (Blue at calibrated opacity) */}
          {underPolygons.map((seg, i) => (
            <polygon
              key={`under-${i}`}
              fill="var(--chart-forecast-line)"
              fillOpacity="var(--chart-under-opacity, 0.14)"
              points={makePolygonPoints(seg)}
            />
          ))}

          {/* Actual Line (2px, round join/cap, drawn UNDER forecast, gaps on null) */}
          {actualSegments.map((seg, i) => (
            <polyline
              key={`act-seg-${i}`}
              fill="none"
              stroke="var(--chart-actual-line)"
              strokeWidth="2"
              strokeLinejoin="round"
              strokeLinecap="round"
              points={seg.join(" ")}
            />
          ))}

          {/* Forecast Line (2.5px, round join/cap, drawn ON TOP of actual, gaps on null) */}
          {forecastSegments.map((seg, i) => (
            <polyline
              key={`fc-seg-${i}`}
              fill="none"
              stroke="var(--chart-forecast-line)"
              strokeWidth="2.5"
              strokeLinejoin="round"
              strokeLinecap="round"
              points={seg.join(" ")}
            />
          ))}

          {/* Labels directly on the curves: Forecast (blue, 13px, 600) and Actual (dark, 13px, 600) */}
          {fcLabelPt && (
            <>
              <text
                x={fcLabelX}
                y={fcLabelY}
                fontSize="13"
                fontWeight="600"
                fill="var(--chart-forecast-line)"
              >
                Forecast
              </text>
              <text
                x={fcLabelX + 72}
                y={actLabelY}
                fontSize="13"
                fontWeight="600"
                fill="var(--chart-actual-line)"
              >
                Actual
              </text>
            </>
          )}

          {/* Tooltip & Inspection Line (pinned on highest forecast point until hover) */}
          {activePt && (
            <g pointerEvents="none">
              <line
                x1={activeX}
                y1={yTop}
                x2={activeX}
                y2={yBottom}
                stroke="var(--chart-axis-line)"
                strokeWidth="1"
                strokeDasharray="3 3"
              />
              {activeActY !== null && (
                <circle
                  cx={activeX}
                  cy={activeActY}
                  r="4.5"
                  fill="var(--chart-actual-line)"
                  stroke="var(--chart-surface)"
                  strokeWidth="2"
                />
              )}
              {activeFcY !== null && (
                <circle
                  cx={activeX}
                  cy={activeFcY}
                  r="4.5"
                  fill="var(--chart-forecast-line)"
                  stroke="var(--chart-surface)"
                  strokeWidth="2"
                />
              )}

              {/* Tooltip Box: surface colour, 1px border, 6px radius, no shadow */}
              <rect
                x={tooltipBoxX}
                y={tooltipBoxY}
                width="262"
                height="40"
                rx="6"
                fill="var(--chart-surface)"
                stroke="var(--chart-border)"
                strokeWidth="1"
              />
              <text
                x={tooltipBoxX + 12}
                y={tooltipBoxY + 17}
                fontSize="12"
                fontWeight="600"
                fill="var(--chart-actual-line)"
              >
                {deliveryDateStr.split(",")[0] || "Fri 16 Jan"} · {activeTimeStr}
              </text>
              <text
                x={tooltipBoxX + 12}
                y={tooltipBoxY + 33}
                fontSize="12"
                fill="var(--chart-text)"
              >
                Forecast{" "}
                {activePt.forecast_mw !== null
                  ? activePt.forecast_mw.toLocaleString()
                  : "—"}{" "}
                · Actual{" "}
                {activePt.actual_mw !== null
                  ? activePt.actual_mw.toLocaleString()
                  : "—"}
                {formattedErrorSign && ` · ${formattedErrorSign} MW`}
              </text>
            </g>
          )}
        </svg>
      </div>

      <div className="chart-footer-strip">
        <span>{missingForecastCount} of 48 half-hours without a forecast</span>
        <span>{missingActualCount} of 48 without an actual</span>
        <span>Error = forecast − actual</span>
      </div>
    </section>
  );
}
