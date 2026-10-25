/**
 * TanStack React Query hooks for Wind Forecast Monitor data (P6-T01).
 */

import { useQuery } from "@tanstack/react-query";
import { api } from "./client";

export function useMeta() {
  return useQuery({
    queryKey: ["meta"],
    queryFn: api.getMeta,
    staleTime: 1000 * 60 * 60, // 1 hour (metadata is static)
  });
}

export function useForecast(deliveryDate, cutoff = "11:00") {
  return useQuery({
    queryKey: ["forecast", deliveryDate, cutoff],
    queryFn: () => api.getForecast(deliveryDate, cutoff),
    enabled: Boolean(deliveryDate),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useAccuracySummary(fromDate, toDate, cutoff = "11:00") {
  return useQuery({
    queryKey: ["accuracy-summary", fromDate, toDate, cutoff],
    queryFn: () => api.getAccuracySummary(fromDate, toDate, cutoff),
    enabled: Boolean(fromDate && toDate),
    staleTime: 1000 * 60 * 5,
  });
}

export function useAccuracyByHorizon(fromDate, toDate) {
  return useQuery({
    queryKey: ["accuracy-by-horizon", fromDate, toDate],
    queryFn: () => api.getAccuracyByHorizon(fromDate, toDate),
    enabled: Boolean(fromDate && toDate),
    staleTime: 1000 * 60 * 5,
  });
}
