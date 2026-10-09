# Weekly analytics: dev-zero

Synthetic weekly analytics report. Changes describe observed source metrics; causal explanations require additional evidence.

Previous: 2026-09-14 to 2026-09-20
Current: 2026-09-21 to 2026-09-27

## search_console

| Metric | Previous | Current | Change | WoW % | Unit | Status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| clicks | 0 | 18 | 18 | unknown | count | zero_baseline |
| impressions | 0 | 297 | 297 | unknown | count | zero_baseline |
| position | unknown | 9.19 | unknown | unknown | position | missing |
| ctr | unknown | 0.060606 | unknown | unknown | ratio | missing |

## posthog

| Metric | Previous | Current | Change | WoW % | Unit | Status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| sessions | 0 | 40 | 40 | unknown | count | zero_baseline |
| users | 0 | 35 | 35 | unknown | count | zero_baseline |
| conversions | 0 | 2 | 2 | unknown | count | zero_baseline |
| conversion_rate | unknown | 0.05 | unknown | unknown | ratio | missing |

## Findings

- search_console clicks has insufficient evidence for a comparable percentage change (zero_baseline). Evidence: search_console.clicks.wow_pct.
- posthog sessions has insufficient evidence for a comparable percentage change (zero_baseline). Evidence: posthog.sessions.wow_pct.

## Limitations

- This report uses synthetic fixture data only. (synthetic_data)
- Search Console clicks and PostHog sessions measure different populations and are not interchangeable. (source_distinction)
- Source metrics contain null values; do not replace them with zero. (missing_values)
- A zero denominator or baseline makes at least one ratio or percentage change undefined. (zero_denominator)
- A zero denominator or baseline makes at least one ratio or percentage change undefined. (zero_denominator)

## Next checks

- Check source collection coverage before drawing conclusions.
- Segment each source by page and acquisition channel before proposing causes.
