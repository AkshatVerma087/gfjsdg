import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  LabelList,
} from "recharts";

function CustomHorizonTooltip({ active, payload, label }) {
  if (!active || !payload || !payload.length) return null;

  const data = payload[0].payload;
  return (
    <div className="dc-tooltip">
      <div className="dc-tooltip-title">Forecast Lead Time: {label}</div>
      <div className="dc-tooltip-body">
        MAE: {data.mae_mw?.toLocaleString()} MW · RMSE: {data.rmse_mw?.toLocaleString()} MW
      </div>
      <div className="dc-tooltip-body" style={{ fontSize: "11px", marginTop: "2px" }}>
        {data.count} half-hours evaluated
      </div>
    </div>
  );
}

export function HorizonChart({ buckets }) {
  const chartData = (buckets || []).map((b) => {
    const m = b.metrics || {};
    return {
      name: b.bucket_name,
      mae_mw: Math.round(m.mae_mw ?? b.mae_mw ?? 0),
      rmse_mw: Math.round(m.rmse_mw ?? b.rmse_mw ?? 0),
      count: m.count ?? b.count ?? 0,
    };
  });

  return (
    <section aria-label="Error by lead time" className="col-left-narrow">
      <h2 className="section-h2">Miss by forecast age</h2>
      <div className="chart-subtitle" style={{ marginBottom: "14px" }}>
        Mean absolute error, by how long before the half-hour the forecast was published
      </div>

      <div style={{ width: "100%", height: 230 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart
            data={chartData}
            margin={{ top: 22, right: 10, left: -10, bottom: 20 }}
          >
            <CartesianGrid stroke="var(--chart-grid)" vertical={false} />
            <XAxis
              dataKey="name"
              stroke="var(--chart-axis)"
              tick={{ fill: "var(--text-muted)", fontSize: 12 }}
              tickLine={false}
              axisLine={{ stroke: "var(--chart-axis)" }}
              label={{
                value: "Hours between publish and half-hour",
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
            <Tooltip content={<CustomHorizonTooltip />} />
            <Bar
              dataKey="mae_mw"
              fill="var(--color-forecast)"
              radius={[3, 3, 0, 0]}
              maxBarSize={52}
            >
              <LabelList
                dataKey="mae_mw"
                position="top"
                fill="var(--text-main)"
                fontSize={12}
                fontWeight={600}
                formatter={(val) => Math.round(val)}
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
