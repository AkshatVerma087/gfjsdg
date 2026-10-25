import { describe, it, expect } from "vitest";
import { parseConfig } from "./config";

describe("Frontend configuration parsing", () => {
  it("accepts empty string as valid same-origin base URL", () => {
    const conf = parseConfig({ VITE_API_BASE_URL: "" });
    expect(conf.apiBaseUrl).toBe("");
  });

  it("accepts undefined as valid same-origin base URL", () => {
    const conf = parseConfig({});
    expect(conf.apiBaseUrl).toBe("");
  });

  it("accepts valid https URL", () => {
    const conf = parseConfig({ VITE_API_BASE_URL: "https://api.example.com" });
    expect(conf.apiBaseUrl).toBe("https://api.example.com");
  });

  it("accepts valid http URL for local dev", () => {
    const conf = parseConfig({ VITE_API_BASE_URL: "http://localhost:8000" });
    expect(conf.apiBaseUrl).toBe("http://localhost:8000");
  });

  it("throws on invalid URL protocol or format", () => {
    expect(() => parseConfig({ VITE_API_BASE_URL: "ftp://invalid-url" })).toThrow(
      "Frontend configuration error"
    );
    expect(() => parseConfig({ VITE_API_BASE_URL: "invalid-string" })).toThrow(
      "Frontend configuration error"
    );
  });
});
