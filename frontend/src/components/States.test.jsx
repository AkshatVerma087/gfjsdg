import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";
import { LoadingSpinner, ErrorBanner, EmptyState } from "./States";

describe("States components", () => {
  it("renders LoadingSpinner with default message", () => {
    render(<LoadingSpinner />);
    expect(screen.getByText(/loading forecast data/i)).toBeInTheDocument();
  });

  it("renders ErrorBanner with message and calls onRetry when clicked", () => {
    const handleRetry = vi.fn();
    const testError = {
      message: "Upstream unavailable",
      requestId: "test-req-123",
    };

    render(<ErrorBanner error={testError} onRetry={handleRetry} />);
    expect(screen.getByText("Upstream unavailable")).toBeInTheDocument();
    expect(screen.getByText(/Request ID: test-req-123/)).toBeInTheDocument();

    const retryBtn = screen.getByRole("button", { name: /retry/i });
    fireEvent.click(retryBtn);
    expect(handleRetry).toHaveBeenCalledOnce();
  });

  it("renders EmptyState with custom title and description", () => {
    render(
      <EmptyState
        title="Custom Empty"
        description="Nothing to display here"
      />
    );
    expect(screen.getByText("Custom Empty")).toBeInTheDocument();
    expect(screen.getByText("Nothing to display here")).toBeInTheDocument();
  });
});
