import '@testing-library/jest-dom/vitest'
import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

afterEach(cleanup) // unmount between tests (auto-cleanup needs vitest globals, which we don't enable)

// Recharts' ResponsiveContainer needs ResizeObserver, which jsdom lacks.
globalThis.ResizeObserver ||= class {
  observe() {}
  unobserve() {}
  disconnect() {}
}
