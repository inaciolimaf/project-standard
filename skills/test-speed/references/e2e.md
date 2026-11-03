# E2E (Playwright)

## One login for the read-only projects

Each test signing in spends a password hash on the API: in Crivo, 380 per run. Log in once in a
`globalSetup` and start every read-only test from the saved state:

```ts
// e2e/global-setup.ts
/** One login for the read-only projects: each test signing in spent a bcrypt on the API, 380 times a run. */
import { request, type FullConfig } from "@playwright/test";
import { EMAIL, PASSWORD, SIGNED_IN } from "./helpers";

export default async function globalSetup(config: FullConfig): Promise<void> {
  const context = await request.newContext({ baseURL: config.projects[0].use.baseURL });
  const answer = await context.post("/api/v1/auth/login", { data: { email: EMAIL, password: PASSWORD } });
  if (!answer.ok()) throw new Error(`e2e login failed (${answer.status()}): ${await answer.text()}`);
  await context.storageState({ path: SIGNED_IN });
  await context.dispose();
}
```

```ts
// e2e/helpers.ts
/** Written by `global-setup.ts`; the read-only projects start every test from it. */
export const SIGNED_IN = "test-results/.signed-in.json";
```

Remove the `beforeEach(signIn)` from those specs. The `flows` project keeps signing in through the
form: the login is one of the flows it tests.

**Pitfall: rotating refresh tokens.** If using a refresh token invalidates it, parallel contexts that
share one `storageState` log each other out. Then either the access token lives long enough for the
run and no test refreshes, or each worker logs in once (a worker-scoped fixture), not each test.
Inkstave logs in per context for this reason.

## Parallel projects

```ts
export default defineConfig({
  globalSetup: "./e2e/global-setup.ts",
  workers: process.env.PLAYWRIGHT_WORKERS ? Number(process.env.PLAYWRIGHT_WORKERS) : 1,
  retries: 0,
  projects: [
    { name: "routes", fullyParallel: true, use: { ...DESKTOP, storageState: SIGNED_IN }, testMatch: /(routes|axe)\.spec\.ts/ },
    { name: "mobile", fullyParallel: true, use: { ...DESKTOP, storageState: SIGNED_IN, viewport: { width: 390, height: 844 } } },
    { name: "flows", testMatch: /flows\/.*\.spec\.ts/ },
  ],
});
```

- **Read-only** projects (route smoke, 390×844, axe) are `fullyParallel` with several workers.
- **Projects that write data** run one test at a time (`PLAYWRIGHT_WORKERS=1` for them in CI), unless
  each test creates and deletes its own data.
- One API process serves every browser context. Past a few workers it saturates and tests start to
  time out. Raise the worker count while the run gets faster, then stop.

## Shards

In CI, split the big projects with a matrix and `--shard`; each shard is a job with its own API and
database:

```yaml
strategy:
  fail-fast: false
  matrix:
    include:
      - { project: routes, shard: 1/3 }
      - { project: routes, shard: 2/3 }
      - { project: routes, shard: 3/3 }
      - { project: mobile, shard: 1/3 }
      - { project: mobile, shard: 2/3 }
      - { project: mobile, shard: 3/3 }
      - { project: flows, shard: 1/1 }
env:
  PLAYWRIGHT_WORKERS: ${{ matrix.project == 'flows' && 1 || 4 }}
steps:
  - run: cd web && npm run e2e -- --project=${{ matrix.project }} --shard=${{ matrix.shard }}
  - uses: actions/upload-artifact@v4
    if: always() && matrix.project == 'mobile'
    with:
      name: captures-390x844-${{ strategy.job-index }}   # one name per shard
      path: web/captures
```

Every shard pays the setup (checkout, deps, fake data, API, build) again. Shard only while the tests
take longer than the setup; past that, more shards only cost runner minutes.

## Browser

`channel: "chrome"` runs the Google Chrome already installed on the `ubuntu-latest` image, so CI
skips `npx playwright install --with-deps chrome`. A project that needs WebKit or Firefox installs
only that browser.

## Waiting

The API is awaited with a `curl` loop on `/health` with a timeout, never `sleep N`. Inside tests,
`expect(...).toBeVisible()` and other web-first assertions, never `waitForTimeout`.
