export function LoadingSpinner({ message = "Loading forecast data..." }) {
  return (
    <div className="state-box" role="status" aria-live="polite">
      <div className="state-spinner" aria-hidden="true" />
      <div className="state-title">Loading</div>
      <p className="state-desc">{message}</p>
    </div>
  );
}

export function ErrorBanner({ error, onRetry }) {
  return (
    <div className="state-box" role="alert" style={{ borderColor: "#D9731A" }}>
      <div className="state-title" style={{ color: "#D9731A" }}>
        Data Unavailable
      </div>
      <p className="state-desc">
        {error?.message || "An unexpected error occurred while loading data."}
      </p>
      {error?.requestId && (
        <p className="state-desc" style={{ fontSize: "11px", marginTop: "4px" }}>
          Request ID: {error.requestId}
        </p>
      )}
      {onRetry && (
        <button className="btn-retry" onClick={onRetry}>
          Retry
        </button>
      )}
    </div>
  );
}

export function EmptyState({
  title = "No data found",
  description = "Try selecting a different date or cutoff time.",
}) {
  return (
    <div className="state-box">
      <div className="state-title">{title}</div>
      <p className="state-desc">{description}</p>
    </div>
  );
}
