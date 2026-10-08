# Weekly analytics: dev-growth

Synthetic weekly analytics report. Changes describe observed source metrics; causal explanations require additional evidence.

Previous: 2026-09-14 to 2026-09-20
Current: 2026-09-21 to 2026-09-27

## search_console

| Metric | Previous | Current | Change | WoW % | Unit | Status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| clicks | 986 | 1232 | 246 | 24.94929 | count | ok |
| impressions | 19716 | 24646 | 4930 | 25.005072 | count | ok |
| position | 6.6 | 6.3 | -0.3 | -4.545455 | position | ok |
| ctr | 0.05001 | 0.049988 | -0.000022 | -0.044623 | ratio | ok |

## posthog

| Metric | Previous | Current | Change | WoW % | Unit | Status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| sessions | 1775 | 2130 | 355 | 20 | count | ok |
| users | 1479 | 1785 | 306 | 20.689655 | count | ok |
| conversions | 89 | 107 | 18 | 20.224719 | count | ok |
| conversion_rate | 0.050141 | 0.050235 | 0.000094 | 0.187266 | ratio | ok |

## Findings

- search_console clicks increased from 986 to 1232 (24.94929% week over week). Evidence: search_console.clicks.previous, search_console.clicks.current, search_console.clicks.wow_pct.
- posthog sessions increased from 1775 to 2130 (20% week over week). Evidence: posthog.sessions.previous, posthog.sessions.current, posthog.sessions.wow_pct.

## Limitations

- This report uses synthetic fixture data only. (synthetic_data)
- Search Console clicks and PostHog sessions measure different populations and are not interchangeable. (source_distinction)

## Next checks

- Check source collection coverage before drawing conclusions.
- Segment each source by page and acquisition channel before proposing causes.
