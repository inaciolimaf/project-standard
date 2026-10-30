# Known gaps

Where Crivo does not meet this standard yet. When one is resolved, delete it.

| # | Gap | Evidence | Fix |
|---|---|---|---|
| 1 | No field metrics | Crivo collects no LCP, INP or CLS from real users; it needs a route to receive them | `web-vitals` plus that route |

The other gaps measured on 2026-10-30 were closed by Crivo's spec 22, which is now the worked example:
initial JS went from one 830 KB chunk to 148 KB gzip.
