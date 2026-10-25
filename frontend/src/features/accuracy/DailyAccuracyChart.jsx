import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ReferenceLine,
} from "recharts";

function CustomDailyTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  const biasSign = data.bias_mw > 0 ? "+" : "";

  return (
    <div className="dc-tooltip">
      <div className="dc-tooltip-title">{label}</div>
      <div className="dc-tooltip-body">
        MAE: {data.mae_mw?.toLocaleString()} MW · Bias: {biasSign}{data.bias_mw?.toLocaleString()} MW
      </div>
      <div className="dc-tooltip-body" style={{ fontSize: "11px", marginTop: "2px" }}>
        {data.n_pairs} half-hours evaluated
      </div>
    </div>
  );
}

export function DailyAccuracyChart({ daily, windowMae = 0 }) {
  const chartData = (daily || []).map((d) => {
    const dateObj = new Date(d.delivery_date + "T00:00:00Z");
    const label = !isNaN(dateObj)
      ? dateObj.toLocaleDateString("en-GB", {
          day: "numeric",
          month: "short",
          timeZone: "UTC",
        })
      : d.delivery_date;

    return {
      delivery_date: d.delivery_date,
      label,
      mae_mw: d.metrics ? Math.round(d.metrics.mae_mw) : 0,
      bias_mw: d.metrics ? Math.round(d.metrics.bias_mw) : 0,
      n_pairs: d.n_pairs,
    };
  });

  return (
    <section aria-label="Error by delivery day" className="col-right-wide">
      <div className="section-header-row" style={{ marginBottom: 0 }}>
        <h2 className="section-h2">Miss by delivery day</h2>
        <span
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            fontSize: "13px",
            color: "var(--text-secondary)",
          }}
        >
          <svg width="22" height="4" aria-hidden="true">
            <line
              x1="0"
              y1="2"
              x2="22"
              y2="2"
              stroke="var(--color-actual)"
              strokeWidth="2"
              strokeDasharray="4 3"
            />
          </svg>
          Window mean {Math.round(windowMae).toLocaleString()} MW
        </span>
      </div>

      <div className="chart-subtitle" style={{ marginBottom: "14px" }}>
        Mean absolute error of the decision-time forecast, MW
      </div>

      <div style={{ width: "100%", height: 230 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 10, right: 10, left: -10, bottom: 20 }}
          >
            <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
            <XAxis
              dataKey="label"
              stroke="var(--chart-axis)"
              tick={{ fill: "var(--text-muted)", fontSize: 11 }}
              interval={Math.max(1, Math.floor(chartData.length / 6))}
              tickLine={false}
              axisLine={{ stroke: "var(--chart-axis)" }}
              label={{
                value: "Delivery day, 2026",
                position: "insideBottom",
                offset: -12,
                fill: "var(--text-muted)",
                fontSize: 12,
              }}
            />
            <YAxis
              stroke="var(--chart-axis)"
              tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              tickLine={false}
              axisLine={false}
            />
            <Tooltip content={<CustomDailyTooltip />} />
            {windowMae > 0 && (
              <ReferenceLine
                y={Math.round(windowMae)}
                stroke="var(--color-actual)"
                strokeDasharray="5 4"
                strokeWidth={1.5}
              />
            )}
            <Bar
              dataKey="mae_mw"
              fill="var(--color-forecast)"
              radius={[2, 2, 0, 0]}
              maxBarSize={18}
            />
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
