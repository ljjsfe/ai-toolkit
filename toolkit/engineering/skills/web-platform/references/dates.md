# Dates, times and durations

Status: `Temporal` is limited — Chrome 144, Edge 144, Firefox 139; no Safari. When
`typeof Temporal === 'undefined'`, dynamically import `temporal-polyfill` (~15 KB min+gz). Importing the polyfill does not set the global; assign `globalThis.Temporal` yourself if
code relies on it. `Intl.DurationFormat` is Newly available since 2025-03-04.

## Pick the type by what the value means

| value | type | why not `Date` |
|---|---|---|
| birthday, due date, billing date | `Temporal.PlainDate` | a `Date` is an instant: `1990-01-01` stored at UTC midnight shows as 31 Dec west of UTC |
| alarm, store hours | `Temporal.PlainTime` | wall-clock, same everywhere |
| card expiry, billing month | `Temporal.PlainYearMonth` | no fake day to overflow |
| anniversary, fixed holiday | `Temporal.PlainMonthDay` | convert with `.toPlainDate({ year })` before arithmetic |
| meeting in a city, renewal, countdown | `Temporal.ZonedDateTime` | DST-aware arithmetic |
| log line, audit event, server timestamp | `Temporal.Instant` | nanosecond precision; `new Date()` truncates to ms and reorders same-millisecond events |

Never use `PlainDateTime` for an event shared across zones; it carries no zone.

## Rules that fix real bugs

- Time zones by IANA name (`America/New_York`), never a fixed offset such as `UTC-5`; offsets
  change with DST and law.
- Combine separate date and time strings with Temporal
  (`Temporal.PlainDate.from(d).toZonedDateTime({ timeZone, plainTime: t })`), not by interpolating
  `` `${d}T${t}` ``. Never build a `Date` from a hand-made ISO string; go through
  `Temporal.Instant` (`epochMilliseconds`, `Temporal.Instant.fromEpochMilliseconds(date.getTime())`).
- Ambiguous or skipped local times at DST changes: `disambiguation: 'reject'` to detect and warn,
  `'compatible'` (default) to pick automatically. Convert zones with `.withTimeZone()`.
- Month arithmetic: `.add({ months: 1 })` clamps 31 Jan to the end of February by default
  (`overflow: 'constrain'`); pass `overflow: 'reject'` to throw instead.
- Differences: `a.until(b)` / `a.since(b)` with `largestUnit` (`ZonedDateTime` defaults to
  `'hour'`) and `smallestUnit`. Compare durations with `Temporal.Duration.compare(d1, d2,
  { relativeTo })`; `relativeTo` is required once months, years or DST days are involved. Past vs
  future: `duration.sign`.
- Sort instants with `Temporal.Instant.compare`; test equality with `.equals()`, not string
  comparison (`Temporal.PlainDate.compare(a, b) === 0` is fine for calendar dates). Do not collapse durations to `total('nanoseconds')` for display — it
  loses precision past ~104 days.
- Temporal objects are immutable: `.add()`, `.with()`, `.round()` return new values, safe in
  reactive state.
- Browser clocks are coarsened: `Temporal.Now.instant()` is ms/µs resolution. Keep the source's
  recorded timestamp; use `performance.now()` for local sub-millisecond intervals.

## Formatting

- Users see `toLocaleString()` / `Intl.DateTimeFormat` / `Intl.DurationFormat`
  (`style: 'long' | 'short' | 'narrow' | 'digital'`); machines get `toString()` (ISO 8601). Never
  hand-assemble `${years}y ${months}m`.
- Read `.year`, `.month`, `.day` from a Plain type rather than parsing `formatToParts()` output.
- `<input type="time">` value: `.toPlainTime().toString({ smallestUnit: 'minute' })`, not `.slice(0, 5)`.

## Non-Gregorian calendars

- Attach the calendar with `.withCalendar('hebrew')` etc.; check `Intl.supportedValuesOf('calendar')`
  first.
- Loop to `monthsInYear` and `daysInMonth`, never 12 and 31; the last month is
  `month === monthsInYear`. Identify months in lunisolar calendars (Hebrew, Chinese) by
  `monthCode`, not `month`; a leap year there can add a whole month.
- Observation-based calendars (some Islamic variants) are approximated by `Intl`; confirm critical
  religious dates with domain experts.
