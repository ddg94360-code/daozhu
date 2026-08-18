# Changelog

All notable changes to 道樞 Dàoshū are documented here. Format follows [Keep a Changelog](https://keepachangelog.com/) and [Semantic Versioning](https://semver.org/).

## [Unreleased]

### Fixed
- `due_reminders` / monthly summaries / study-note review dates now share `memory_store.now()` (via `_wall_clock` seam). Tests freeze time by patching `_wall_clock`; the previous wall-clock leak made `test_due_reminders_filters_by_time` fail after 2026-08-14.
- `mark_reminder_done` and `check_shopping` now update in place (`done` / `checked`) instead of deleting the record.
- Health streak requires calendar-adjacent days (a skipped day breaks the streak).
- Energy insight threshold reads `energy_analysis_days` from config instead of a hardcoded 7.

### Added
- 本機儀表板第二期：筆記 CRUD、決策寫入、道藏只讀、感知條（記憶推斷）、內閣組閣預覽、心鏡 JSON 播放、統一 500 handler
- `daily.mark_study_note_reviewed_by_id` / `daily.delete_study_note_by_id`（MCP 同名）；新筆記帶 `id`
- `memory_store.map_update` — in-place record transform (the missing primitive behind mark-done / check / reviewed).
- `daozhu_mark_study_note_reviewed` — mark a study note as reviewed so it leaves the due list.
- `config.py` — optional `config.yaml` support (`timezone`, `currency`, `review_weekday`, `review_time`, `energy_analysis_days`, `high_speed_threshold`), with `config.yaml.example`
- `daozhu_export_expenses_csv` — export monthly expenses as CSV (auto-escapes commas)
- `daozhu_config_show` — inspect the active configuration
- Health log now returns `consecutive_days` (streak of days with sleep/exercise)
- Expense responses and weekly report now carry a `currency` symbol from config
- Weekly report reuses the already-fetched week's mood records for energy insight (one fewer file read)

### Tests
- Expanded 20 → 42: CONFIG loading, CSV export, health calendar-adjacency, energy-insight config threshold, map_update, mark-done / check-shopping / mark-reviewed keep records, solar-term across 2025–2027 and the cross-year boundary
- Dashboard: other-month expenses, list GETs, `/static` 200, loopback ignores `X-Forwarded-For`

### Docs
- English README (`README.md`) + Traditional Chinese (`README.zh-TW.md`) with language switcher
- `CONTRIBUTING.md`, `CHANGELOG.md`, `NOTICE`
- GitHub Actions CI (pytest across Python 3.10–3.13)
- Project badges (license, Python, CI)

## [1.0.0] — 2026-08-12

Initial open-source release.

### Added
- **Perception network** — 7 layers: emotion / task / interpersonal / complexity / concise-mode / tone / energy
- **Cabinet** — Confucian, Taoist, Legalist, Strategist schools + Military, Mohist, Buddhist patches
- **Skill modules** — Work Guide (百工鑑), Virtual Masters (百師錄), Music Companion (弦外之音), Metaphysical Mirror (萬象心鏡, 7 modes), Solar Terms (陰陽時令), Cabinet Meeting (內閣會議), Skill Routing
- **Memory layer MCP** — expense, health, reminders, shopping, mood journal, study notes, decision log, weekly report, energy insight, strategy vault (道藏), solar-term calendar
- Atomic JSON storage (`memory_store`) with corrupt-file backup, shared clock, subdir collections
- 31 tests across 4 suites
