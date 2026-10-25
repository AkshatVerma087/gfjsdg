import "@testing-library/jest-dom";

// Polyfill ResizeObserver for JSDOM / Recharts
globalThis.ResizeObserver = class ResizeObserver {
  observe() {}
  unobserve() {}
  disconnect() {}
};
