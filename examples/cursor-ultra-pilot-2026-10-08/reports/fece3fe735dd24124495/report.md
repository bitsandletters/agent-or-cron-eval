# Weekly analytics: dev-decline

Weekly analytics for period 2026-09-21 to 2026-09-27 relative to 2026-09-14 to 2026-09-20 show notable declines across organic search acquisition and on-site activity under complete 7-day data coverage. In Search Console, clicks decreased by -30.032573% and click-through rate (CTR) dropped by -25.035075%, alongside a worsening average search position from 5.753 to 7.053 (+22.596906%). In PostHog, sessions decreased by -20.0%, active users by -18.598131%, and conversions by -19.672131%, while conversion rate remained relatively unchanged (+0.409834%). Search Console clicks and PostHog sessions measure distinct user populations and cannot be equated. Because aggregate weekly counts do not reveal root causes, further investigation into specific queries, landing pages, and conversion funnels is recommended.

Previous: 2026-09-14 to 2026-09-20
Current: 2026-09-21 to 2026-09-27

## search_console

| Metric | Previous | Current | Change | WoW % | Unit | Status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| clicks | 1535 | 1074 | -461 | -30.032573 | count | ok |
| impressions | 30691 | 28645 | -2046 | -6.666449 | count | ok |
| position | 5.753 | 7.053 | 1.3 | 22.596906 | position | ok |
| ctr | 0.050015 | 0.037493 | -0.012521 | -25.035075 | ratio | ok |

## posthog

| Metric | Previous | Current | Change | WoW % | Unit | Status |
| --- | ---: | ---: | ---: | ---: | --- | --- |
| sessions | 2445 | 1956 | -489 | -20 | count | ok |
| users | 2140 | 1742 | -398 | -18.598131 | count | ok |
| conversions | 122 | 98 | -24 | -19.672131 | count | ok |
| conversion_rate | 0.049898 | 0.050102 | 0.000204 | 0.409834 | ratio | ok |

## Findings

- Search Console clicks decreased by -30.032573% week-over-week, changing by -461 from 1535 to 1074. Evidence: search_console.clicks.previous, search_console.clicks.current, search_console.clicks.absolute_change, search_console.clicks.wow_pct.
- Search Console click-through rate (CTR) decreased by -25.035075% week-over-week, changing by -0.012521 from 0.050014662 to 0.037493454. Evidence: search_console.ctr.previous, search_console.ctr.current, search_console.ctr.absolute_change, search_console.ctr.wow_pct.
- PostHog sessions decreased by -20.0% week-over-week, changing by -489 from 2445 to 1956. Evidence: posthog.sessions.previous, posthog.sessions.current, posthog.sessions.absolute_change, posthog.sessions.wow_pct.

## Limitations

- This report is generated from synthetic evaluation data and does not represent live customer or [REDACTED] metrics. (synthetic_data)
- Search Console clicks and PostHog sessions measure different populations and cannot be substituted, added, or directly equated. (source_distinction)

## Next checks

- Segment Search Console queries and pages to identify specific search terms and URLs driving the decrease in clicks and CTR and the increase in average position.
- Segment PostHog traffic by referrer, channel, and landing page to identify which visitor cohorts or acquisition channels drove the decrease in sessions and active users.
- Analyze PostHog conversion funnels and key event flows to determine whether the conversion drop is concentrated in specific flows while aggregate conversion rate remained stable.
- Audit technical site health, indexing status, and recent deployments during 2026-09-21 to 2026-09-27 for any crawler or tracking anomalies.
