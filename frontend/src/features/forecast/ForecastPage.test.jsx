import { render, screen } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ForecastPage } from "./ForecastPage";
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

describe("ForecastPage Component", () => {
  it("renders loading state when query is loading", () => {
    hooks.useMeta.mockReturnValue({ data: null });
    hooks.useForecast.mockReturnValue({
      data: null,
      isLoading: true,
      isError: false,
    });

    renderWithClient(<ForecastPage />);
    expect(screen.getByRole("status")).toBeInTheDocument();
  });

  it("renders error banner when query fails", () => {
    hooks.useMeta.mockReturnValue({ data: null });
    hooks.useForecast.mockReturnValue({
      data: null,
      isLoading: false,
      isError: true,
      error: { message: "Failed to connect to API" },
      refetch: vi.fn(),
    });

    renderWithClient(<ForecastPage />);
    expect(screen.getByText("Failed to connect to API")).toBeInTheDocument();
  });

  it("renders forecast controls and KPIs when data is loaded", () => {
    hooks.useMeta.mockReturnValue({
      data: {
        data_window_start: "2025-12-30",
        data_window_end: "2026-02-03",
        default_cutoff_time: "11:00",
      },
    });

    hooks.useForecast.mockReturnValue({
      data: {
        delivery_date: "2026-01-16",
        cutoff_time: "09:00",
        total_periods: 48,
        missing_forecast_count: 0,
        missing_actual_count: 0,
        points: [
          {
            settlement_period: 1,
            start_time: "2026-01-16T00:00:00Z",
            forecast_mw: 5000,
            actual_mw: 4850,
            publish_time: "2026-01-15T08:30:00Z",
            lead_time_hours: 15.5,
          },
          {
            settlement_period: 2,
            start_time: "2026-01-16T00:30:00Z",
            forecast_mw: 5200,
            actual_mw: 5100,
            publish_time: "2026-01-15T08:30:00Z",
            lead_time_hours: 16.0,
          },
        ],
      },
      isLoading: false,
      isError: false,
    });

    renderWithClient(<ForecastPage />);
    expect(screen.getByText("Wind forecast at decision time")).toBeInTheDocument();
    expect(screen.getByText("Forecast used")).toBeInTheDocument();
    expect(screen.getByText("Average forecast")).toBeInTheDocument();
    expect(screen.getByText("Lowest half-hour")).toBeInTheDocument();
    expect(screen.getByText("Average miss, this day")).toBeInTheDocument();
    expect(screen.getByText("Show all 48 half-hours in table ▼")).toBeInTheDocument();
  });
});
