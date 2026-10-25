import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AccuracyPage } from "./AccuracyPage";
import * as hooks from "../../api/hooks";

vi.mock("../../api/hooks");

function renderWithClient(ui) {
  const testClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return render(
    <QueryClientProvider client={testClient}>{ui}</QueryClientProvider>
  );
}

describe("AccuracyPage Component", () => {
  it("renders loading state when query is loading", () => {
    hooks.useMeta.mockReturnValue({ data: null });
    hooks.useAccuracySummary.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });
    hooks.useAccuracyByHorizon.mockReturnValue({
      data: null,
      isLoading: false,
      isError: false,
    });

    renderWithClient(<AccuracyPage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders accuracy KPIs and over-forecast risk", () => {
    hooks.useMeta.mockReturnValue({
      data: {
        data_window_start: "2025-12-30",
        data_window_end: "2026-02-03",
      },
    });

    hooks.useAccuracySummary.mockReturnValue({
      data: {
        start_date: "2026-01-02",
        end_date: "2026-02-01",
        cutoff_time: "09:00",
        total_evaluated_periods: 1488,
        total_missing_forecasts: 0,
        total_missing_actuals: 0,
        overall: {
          count: 1488,
          bias_mw: 118.0,
          mae_mw: 350.0,
          rmse_mw: 462.0,
          p50_abs_error_mw: 280.0,
          p90_abs_error_mw: 820.0,
          p95_abs_error_mw: 1040.0,
          wape_pct: 4.4,
          over_forecast_count: 863,
          over_forecast_pct: 58.0,
          under_forecast_count: 625,
          under_forecast_pct: 42.0,
          exact_count: 0,
          p90_over_forecast_mw: 610.0,
        },
        daily: [],
      },
      isLoading: false,
      isError: false,
    });

    hooks.useAccuracyByHorizon.mockReturnValue({
      data: { buckets: [] },
      isLoading: false,
      isError: false,
    });

    renderWithClient(<AccuracyPage />);
    expect(screen.getByText("Forecast accuracy")).toBeInTheDocument();
    expect(screen.getAllByText("Mean absolute error")[0]).toBeInTheDocument();
    expect(screen.getAllByText("Bias")[0]).toBeInTheDocument();
    expect(screen.getByText("Over-forecast risk")).toBeInTheDocument();
    expect(screen.getByText("How to read these numbers")).toBeInTheDocument();
  });
});
