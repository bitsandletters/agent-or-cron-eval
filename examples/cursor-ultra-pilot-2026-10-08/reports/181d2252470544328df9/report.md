# Weekly analytics: dev-growth

Both weeks are complete, so week-over-week comparisons are available. The week of 2026-09-21 to 2026-09-27 is a volume story in both sources, with rates nearly unchanged. Search Console impressions rose 25.005072% (4930) and clicks rose 24.94929% (246), while CTR moved from 0.050010144 to 0.049987828 (-0.044623%) and average position moved from 6.6 to 6.3 (-4.545455%). PostHog sessions rose 20.0% (355), users rose 20.689655% (306), and conversions rose 20.224719% (18), while conversion rate moved from 0.050140845 to 0.050234742 (0.187266%). Search Console clicks and PostHog sessions count different populations and are not combined. These weekly totals do not show why volume rose.

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

- Search Console impressions increased from 19716 to 24646, a change of 4930, or 25.005072%. This is the largest supported week-over-week move in the report. Evidence: search_console.impressions.previous, search_console.impressions.current, search_console.impressions.absolute_change, search_console.impressions.wow_pct.
- Search Console clicks increased from 986 to 1232, a change of 246, or 24.94929%. Evidence: search_console.clicks.previous, search_console.clicks.current, search_console.clicks.absolute_change, search_console.clicks.wow_pct.
- PostHog conversions increased from 89 to 107, a change of 18, or 20.224719%. Evidence: posthog.conversions.previous, posthog.conversions.current, posthog.conversions.absolute_change, posthog.conversions.wow_pct.

## Limitations

- All figures come from the synthetic dev-growth fixture. They are not live Search Console or PostHog measurements and do not describe a real property. (synthetic_data)
- Search Console clicks and PostHog sessions count different populations. This report does not add, substitute, or equate them. (source_distinction)

## Next checks

- Split Search Console impressions and clicks by query, page, and device to see whether the impression increase of 4930 and the click increase of 246 are broad or concentrated. Weekly totals do not show which queries moved.
- Split PostHog sessions, users, and conversions by day and landing page. Sessions rose by 355, users by 306, and conversions by 18, while conversion rate changed by only 0.187266%, so check whether the conversion increase is spread across the week.
- Keep Search Console clicks and PostHog sessions in separate breakdowns. A channel or landing-page view inside PostHog can sit alongside Search Console, but the two counts should stay uncombined.
- Check average position by query. The aggregate moved from 6.6 to 6.3, a change of -0.3 (-4.545455%). Query-level positions would show whether that improvement is widespread.
- CTR changed by -0.000022 (-0.044623%). Treat a sitewide CTR review as lower priority than the volume breakdown unless query mix changed.
