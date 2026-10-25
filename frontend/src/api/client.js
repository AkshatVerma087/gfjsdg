/**
 * API client for the Wind Forecast Monitor API (P6-T01).
 * Handles request-ID propagation, timeout, and structured error responses.
 */

import { config } from "../config";

function generateRequestId() {
  return "req-" + Math.random().toString(36).substring(2, 10);
}

async function request(endpoint, options = {}) {
  const url = `${config.apiBaseUrl}${endpoint}`;
  const requestId = generateRequestId();

  const headers = {
    Accept: "application/json",
    "X-Request-ID": requestId,
    ...options.headers,
  };

  try {
    const response = await fetch(url, { ...options, headers });
    const data = await response.json().catch(() => null);

    if (!response.ok) {
      const code = data?.error?.code || `HTTP_${response.status}`;
      const message =
        data?.error?.message ||
        `Request failed with status ${response.status} (${response.statusText})`;
      const error = new Error(message);
      error.code = code;
      error.status = response.status;
      error.requestId = data?.error?.request_id || requestId;
      throw error;
    }

    return data;
  } catch (err) {
    if (!err.code) {
      err.code = "NETWORK_ERROR";
      err.message = err.message || "Failed to communicate with API server.";
    }
    throw err;
  }
}

export const api = {
  getMeta: () => request("/api/v1/meta"),

  getForecast: (deliveryDate, cutoff = "11:00") => {
    const params = new URLSearchParams({
      delivery_date: deliveryDate,
      cutoff,
    });
    return request(`/api/v1/forecast?${params.toString()}`);
  },

  getAccuracySummary: (fromDate, toDate, cutoff = "11:00") => {
    const params = new URLSearchParams();
    if (fromDate) params.set("from_date", fromDate);
    if (toDate) params.set("to_date", toDate);
    if (cutoff) params.set("cutoff", cutoff);
    return request(`/api/v1/accuracy/summary?${params.toString()}`);
  },

  getAccuracyByHorizon: (fromDate, toDate) => {
    const params = new URLSearchParams();
    if (fromDate) params.set("from_date", fromDate);
    if (toDate) params.set("to_date", toDate);
    return request(`/api/v1/accuracy/by-horizon?${params.toString()}`);
  },
};
