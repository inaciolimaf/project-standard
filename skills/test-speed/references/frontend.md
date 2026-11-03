# Frontend (Vitest)

## Pool and workers

```ts
// vite.config.ts
test: {
  environment: "jsdom",
  // 110 s against 151 s of the default forks on two CPUs, the size of the CI runner.
  pool: "threads",
  ...
}
```

- `threads` is faster than the default `forks` for jsdom suites. Switch back only for a test that
  needs process isolation (native modules, `process.chdir`).
- Vitest's default is CPUs − 1 workers: **one** on a 2-CPU GitHub runner. In CI pass
  `--maxWorkers=3` (`npm run coverage -- --maxWorkers=3`); jsdom tests wait on the event loop often
  enough that a third worker pays off. A cap in the config (`poolOptions.threads.maxThreads`) also
  works when the value should be the same everywhere.

## Waiting

- Fake timers for time, debounce and animation, never `waitFor` on real time.
- The wait for async UI lives in one place (`configure({ asyncUtilTimeout })` in `setup.ts`), not in
  each file. A screen test waits for the lazy route it opened, not only for `main`.

## Coverage

The coverage run is the test run in CI (`npm run coverage`), not a second pass over the suite.
